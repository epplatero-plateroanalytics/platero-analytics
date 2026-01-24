import tempfile
from datetime import datetime

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from fpdf import FPDF

COR_AZUL = (0, 51, 102)
COR_CINZA = (85, 85, 85)
COR_TEXTO = (40, 40, 40)


class PDF(FPDF):
    def header(self):
        self.set_font("Helvetica", 'B', 14)
        self.set_text_color(*COR_AZUL)
        self.cell(0, 8, "Relatório Executivo - Platero Analytics", ln=True, align="L")

        self.set_font("Helvetica", '', 9)
        self.set_text_color(*COR_CINZA)
        data_str = datetime.now().strftime('%d/%m/%Y %H:%M')
        self.cell(0, 6, f"Gerado em {data_str}", ln=True, align="L")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", '', 8)
        self.set_text_color(*COR_CINZA)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", 0, 0, 'C')

    def titulo(self, texto):
        self.set_font("Helvetica", 'B', 12)
        self.set_text_color(*COR_AZUL)
        self.ln(4)
        
        # --- CORREÇÃO: Limpeza de caracteres incompatíveis ---
        # Garante que emojis ou aspas especiais não quebrem o PDF
        if texto:
            texto = texto.encode('latin-1', 'replace').decode('latin-1')
        # -----------------------------------------------------

        self.cell(0, 8, texto, ln=True)
        self.set_draw_color(200, 200, 200)
        y = self.get_y()
        self.line(10, y, 200, y)
        self.ln(3)

    def paragrafo(self, texto):
        self.set_font("Helvetica", '', 10)
        self.set_text_color(*COR_TEXTO)

        # --- CORREÇÃO: Limpeza de caracteres incompatíveis ---
        # Converte caracteres que o FPDF não aceita (ex: emojis) em '?'
        if texto:
            texto = texto.encode('latin-1', 'replace').decode('latin-1')
        # -----------------------------------------------------

        self.multi_cell(0, 5, texto)
        self.ln(2)

    def inserir_figura(self, fig, largura=170):
        if fig is None:
            return
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            fig.savefig(tmp.name, dpi=120, bbox_inches="tight")
            self.image(tmp.name, x=15, w=largura)


def fmt_num(x):
    try:
        return f"{float(x):,.2f}"
    except:
        return str(x)


def gerar_pdf_pro(
    df_original,
    df_limpo,
    datas,
    numericas,
    categoricas,
    figs_principais,
    texto_ia,
    usuario="Cliente"
):
    pdf = PDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.alias_nb_pages()

    # CAPA
    pdf.add_page()
    pdf.set_font("Helvetica", 'B', 20)
    pdf.set_text_color(*COR_AZUL)
    pdf.ln(40)
    pdf.cell(0, 10, "Relatório Executivo", ln=True, align="C")

    pdf.set_font("Helvetica", '', 12)
    pdf.set_text_color(*COR_CINZA)
    pdf.ln(5)
    
    # Limpeza também no nome do cliente por segurança
    if usuario:
        usuario = usuario.encode('latin-1', 'replace').decode('latin-1')
        
    pdf.cell(0, 8, f"Cliente: {usuario}", ln=True, align="C")

    # RESUMO / KPIs
    pdf.add_page()
    pdf.titulo("Resumo numérico")

    if numericas:
        col_valor = numericas[0]
        serie = pd.to_numeric(df_limpo[col_valor], errors="coerce")
        total = serie.sum(skipna=True)
        media = serie.mean(skipna=True)
        minimo = serie.min(skipna=True)
        maximo = serie.max(skipna=True)
        desvio = serie.std(skipna=True)

        texto = (
            f"Coluna analisada: {col_valor}\n\n"
            f"• Total: {fmt_num(total)}\n"
            f"• Média: {fmt_num(media)}\n"
            f"• Mínimo: {fmt_num(minimo)}\n"
            f"• Máximo: {fmt_num(maximo)}\n"
            f"• Desvio padrão: {fmt_num(desvio)}\n"
            f"• Registros: {len(df_limpo)}"
        )
        pdf.paragrafo(texto)
    else:
        pdf.paragrafo("Nenhuma coluna numérica foi identificada para cálculo de KPIs.")

    # GRÁFICOS PRINCIPAIS
    if figs_principais:
        pdf.titulo("Gráficos principais")
        for fig in figs_principais:
            pdf.inserir_figura(fig)
            pdf.ln(5)

    # TEXTO DA IA
    pdf.add_page()
    pdf.titulo("Parecer da Inteligência Artificial")

    if texto_ia:
        pdf.paragrafo(texto_ia)
    else:
        pdf.paragrafo("Nenhum parecer de IA foi fornecido para esta análise.")

    # EXPORTAÇÃO DO PDF
    pdf_bytes = pdf.output()  
    return pdf_bytes
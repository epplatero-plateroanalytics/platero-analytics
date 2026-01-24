import tempfile
import os
import requests
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
    def __init__(self, orientation="P", unit="mm", format="A4"):
        super().__init__(orientation=orientation, unit=unit, format=format)
        self.use_unicode = False  # Flag para saber se estamos usando Unicode

    def header(self):
        font = "DejaVu" if self.use_unicode else "Helvetica"
        self.set_font(font, 'B', 14)
        self.set_text_color(*COR_AZUL)
        self.cell(0, 8, "Relatório Executivo - Platero Analytics", ln=True, align="L")

        self.set_font(font, '', 9)
        self.set_text_color(*COR_CINZA)
        data_str = datetime.now().strftime('%d/%m/%Y %H:%M')
        self.cell(0, 6, f"Gerado em {data_str}", ln=True, align="L")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        font = "DejaVu" if self.use_unicode else "Helvetica"
        self.set_font(font, '', 8)
        self.set_text_color(*COR_CINZA)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", 0, 0, 'C')

    def titulo(self, texto):
        font = "DejaVu" if self.use_unicode else "Helvetica"
        self.set_font(font, 'B', 12)
        self.set_text_color(*COR_AZUL)
        self.ln(4)
        
        # Limpeza de segurança
        if not self.use_unicode:
            texto = sanitize_text(texto)
            
        self.cell(0, 8, texto, ln=True)
        self.set_draw_color(200, 200, 200)
        y = self.get_y()
        self.line(10, y, 200, y)
        self.ln(3)

    def paragrafo(self, texto):
        font = "DejaVu" if self.use_unicode else "Helvetica"
        self.set_font(font, '', 10)
        self.set_text_color(*COR_TEXTO)
        
        # Limpeza de segurança se não tivermos fonte Unicode
        if not self.use_unicode:
            texto = sanitize_text(texto)
            
        self.multi_cell(0, 5, texto)
        self.ln(2)

    def inserir_figura(self, fig, largura=170):
        if fig is None:
            return
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            fig.savefig(tmp.name, dpi=120, bbox_inches="tight")
            self.image(tmp.name, x=15, w=largura)

def sanitize_text(text):
    """
    Remove caracteres que quebram a fonte Helvetica/Latin-1.
    Substitui bullets e aspas curvas por equivalentes simples.
    """
    if not text:
        return ""
    
    # Substituições manuais comuns
    replacements = {
        "•": "-",      # Bullet point vira traço
        "“": '"',      # Aspas curvas
        "”": '"',
        "‘": "'",
        "’": "'",
        "–": "-",      # En-dash
        "—": "-",      # Em-dash
        "…": "...",
        "📊": "",      # Remove emojis comuns
        "📈": "",
        "📉": "",
        "🤖": "",
        "✨": ""
    }
    
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
        
    # Garante que é Latin-1 compatível
    return text.encode('latin-1', 'replace').decode('latin-1')

def fmt_num(x):
    try:
        return f"{float(x):,.2f}"
    except:
        return str(x)

def check_download_font():
    """Tenta baixar a fonte. Retorna o caminho se existir."""
    font_path = "DejaVuSans.ttf"
    if not os.path.exists(font_path):
        url = "https://github.com/reingart/pyfpdf/raw/master/fpdf/font/DejaVuSans.ttf"
        try:
            r = requests.get(url, allow_redirects=True, timeout=5)
            with open(font_path, 'wb') as f:
                f.write(r.content)
        except:
            return None # Falha no download
    return font_path if os.path.exists(font_path) else None

def gerar_pdf_pro(
    df_original,
    df_limpo,
    datas,
    numericas,
    categoricas,
    figs_principais,
    texto_ia,
    usuario="Cliente",
    coluna_alvo=None
):
    pdf = PDF(orientation="P", unit="mm", format="A4")
    
    # 1. Tenta carregar fonte Unicode
    font_path = check_download_font()
    if font_path:
        try:
            pdf.add_font("DejaVu", "", font_path)
            pdf.add_font("DejaVu", "B", font_path)
            pdf.use_unicode = True
        except Exception:
            pdf.use_unicode = False # Fallback se o arquivo estiver corrompido
    else:
        pdf.use_unicode = False

    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.alias_nb_pages()

    # CAPA
    pdf.add_page()
    
    font_capa = "DejaVu" if pdf.use_unicode else "Helvetica"
    pdf.set_font(font_capa, 'B', 20)
    pdf.set_text_color(*COR_AZUL)
    pdf.ln(40)
    pdf.cell(0, 10, "Relatório Executivo", ln=True, align="C")

    pdf.set_font(font_capa, '', 12)
    pdf.set_text_color(*COR_CINZA)
    pdf.ln(5)
    
    if not pdf.use_unicode:
        usuario = sanitize_text(usuario)
        
    pdf.cell(0, 8, f"Cliente: {usuario}", ln=True, align="C")

    # RESUMO / KPIs
    pdf.add_page()
    pdf.titulo("Resumo numérico")

    # LÓGICA DE COLUNA
    col_valor = None
    if coluna_alvo and coluna_alvo in df_limpo.columns:
         if pd.api.types.is_numeric_dtype(df_limpo[coluna_alvo]):
             col_valor = coluna_alvo
    
    if not col_valor and numericas:
        col_valor = numericas[0]

    if col_valor:
        serie = pd.to_numeric(df_limpo[col_valor], errors="coerce")
        total = serie.sum(skipna=True)
        media = serie.mean(skipna=True)
        minimo = serie.min(skipna=True)
        maximo = serie.max(skipna=True)
        desvio = serie.std(skipna=True)

        # Usamos traço (-) em vez de bullet (•) no texto base para garantir compatibilidade
        texto = (
            f"Coluna analisada: {col_valor}\n\n"
            f"- Total: {fmt_num(total)}\n"
            f"- Média: {fmt_num(media)}\n"
            f"- Mínimo: {fmt_num(minimo)}\n"
            f"- Máximo: {fmt_num(maximo)}\n"
            f"- Desvio padrão: {fmt_num(desvio)}\n"
            f"- Registros: {len(df_limpo)}"
        )
        pdf.paragrafo(texto)
    else:
        pdf.paragrafo("Nenhuma coluna numérica válida identificada para KPIs.")

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
        pdf.paragrafo("Nenhum parecer de IA foi fornecido.")

    return bytes(pdf.output())
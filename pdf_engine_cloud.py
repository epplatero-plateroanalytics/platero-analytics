from fpdf import FPDF
import matplotlib.pyplot as plt
import os
import tempfile
import pandas as pd

class PDF(FPDF):
    def header(self):
        # Marca d'água
        self.set_text_color(240, 240, 240)
        self.set_font('Arial', 'B', 48)
        self.set_xy(0, 100)
        self.cell(0, 10, 'PLATERO ANALYTICS', align='C')

        # Logotipo
        if os.path.exists('logo.png'):
            self.image('logo.png', 10, 8, w=30)

        # Título
        self.set_y(15)
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, 'Relatório Executivo Completo', 0, 1, 'R')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Platero Analytics - Página {self.page_no()}', 0, 0, 'C')


def gerar_pdf(df, df_filtrado, datas, numericas, categoricas, figs, lang="pt"):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # ============================================================
    # 1. RESUMO EXECUTIVO
    # ============================================================
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "1. Resumo Executivo", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", size=11)

    # --- BLINDAGEM NUMÉRICA ---
    if numericas:
        col = numericas[0]
        serie = pd.to_numeric(df[col], errors="coerce")
        total_val = serie.sum(skipna=True)
        media_val = serie.mean(skipna=True)
    else:
        total_val = 0
        media_val = 0

    pdf.cell(0, 8, f"Total de Registros Analisados: {len(df)}", ln=True)
    pdf.cell(0, 8, f"Volume Total Processado: {total_val:,.2f}", ln=True)
    pdf.cell(0, 8, f"Ticket Médio: {media_val:,.2f}", ln=True)
    pdf.ln(5)

    # ============================================================
    # 2. RANKING / FIGURA 1
    # ============================================================
    if len(figs) > 0:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "2. Análise de Ranking (Top Performers)", ln=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            figs[0].savefig(tmp.name, dpi=100, bbox_inches='tight')
            pdf.image(tmp.name, x=10, w=190)

    # ============================================================
    # 3. TENDÊNCIAS E SHARE
    # ============================================================
    if len(figs) > 1:
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "3. Análise Temporal e Mercado", ln=True)
        pdf.ln(5)

        # Linha do tempo
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            figs[1].savefig(tmp.name, dpi=100, bbox_inches='tight')
            pdf.image(tmp.name, x=10, w=180)
        pdf.ln(5)

        # Pizza
        if len(figs) > 2:
            pdf.cell(0, 10, "Share de Mercado (Top 5)", ln=True)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                figs[2].savefig(tmp.name, dpi=100, bbox_inches='tight')
                pdf.image(tmp.name, x=40, w=130)

    # ============================================================
    # 4. ESTATÍSTICA AVANÇADA
    # ============================================================
    if len(figs) > 3:
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "4. Análise Estatística Avançada", ln=True)
        pdf.ln(5)

        # Boxplot
        pdf.cell(0, 10, "Distribuição e Variabilidade (Boxplot)", ln=True)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            figs[3].savefig(tmp.name, dpi=100, bbox_inches='tight')
            pdf.image(tmp.name, x=10, w=180)
        pdf.ln(5)

        # Heatmap
        if len(figs) > 4:
            pdf.cell(0, 10, "Mapa de Correlação (Heatmap)", ln=True)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                figs[4].savefig(tmp.name, dpi=100, bbox_inches='tight')
                pdf.image(tmp.name, x=50, w=110)

    # ============================================================
    # 5. PARECER DA IA
    # ============================================================
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "5. Parecer da Inteligência Artificial", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", size=11)
    import streamlit as st
    texto = st.session_state.get("analise_texto", "Análise não gerada.")
    pdf.multi_cell(0, 7, txt=texto)

    return pdf.output(dest='S').encode('latin-1')
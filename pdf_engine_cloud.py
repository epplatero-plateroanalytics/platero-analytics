from fpdf import FPDF
import matplotlib.pyplot as plt
import os
import tempfile

class PDF(FPDF):
    def header(self):
        # --- MARCA D'ÁGUA ---
        self.set_text_color(245, 245, 245)  
        self.set_font('Arial', 'B', 50)
        self.set_xy(0, 100) 
        self.cell(0, 10, 'PLATERO ANALYTICS', align='C')
        
        # --- LOGOTIPO ---
        if os.path.exists('logo.png'):
            self.image('logo.png', 10, 8, w=30)

        # --- TÍTULO ---
        self.set_y(15) 
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 0, 0) 
        self.cell(0, 10, 'Relatorio Executivo Completo', 0, 1, 'R')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Platero Analytics - Pagina {self.page_no()}', 0, 0, 'C')

def gerar_pdf(df, df_filtrado, datas, numericas, categoricas, figs, lang="pt"):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- PÁGINA 1: RESUMO E RANKING ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "1. Resumo Executivo", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", size=11)
    if numericas:
    col = numericas[0]
    serie = pd.to_numeric(df[col], errors="coerce")

    if serie.notna().sum() == 0:
        total_val = 0
        media_val = 0
    else:
        total_val = serie.sum()
        media_val = serie.mean()
else:
    total_val = 0
    media_val = 0
    
    pdf.cell(0, 8, f"Total de Registros Analisados: {len(df)}", ln=True)
    pdf.cell(0, 8, f"Volume Total Processado: {total_val:,.2f}", ln=True)
    pdf.cell(0, 8, f"Ticket Medio: {media_val:,.2f}", ln=True)
    pdf.ln(5)

    if len(figs) > 0:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "2. Analise de Ranking (Top Performers)", ln=True)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        figs[0].savefig(temp_file.name, dpi=100, bbox_inches='tight')
        pdf.image(temp_file.name, x=10, w=190)

    # --- PÁGINA 2: TENDÊNCIAS E SHARE ---
    if len(figs) > 1:
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "3. Analise Temporal e Mercado", ln=True)
        pdf.ln(5)

        # Linha do Tempo
        temp_file2 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        figs[1].savefig(temp_file2.name, dpi=100, bbox_inches='tight')
        pdf.image(temp_file2.name, x=10, w=180)
        pdf.ln(5)

        # Pizza
        if len(figs) > 2:
            pdf.cell(0, 10, "Share de Mercado (Top 5)", ln=True)
            temp_file3 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            figs[2].savefig(temp_file3.name, dpi=100, bbox_inches='tight')
            pdf.image(temp_file3.name, x=40, w=130)

    # --- PÁGINA 3: ESTATÍSTICA AVANÇADA (NOVA!) ---
    if len(figs) > 3:
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "4. Analise Estatistica Avancada", ln=True)
        pdf.ln(5)

        # Boxplot
        pdf.cell(0, 10, "Distribuicao e Variabilidade (Boxplot)", ln=True)
        temp_file4 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        figs[3].savefig(temp_file4.name, dpi=100, bbox_inches='tight')
        pdf.image(temp_file4.name, x=10, w=180)
        pdf.ln(5)

        # Heatmap
        if len(figs) > 4:
            pdf.cell(0, 10, "Mapa de Correlacao (Heatmap)", ln=True)
            temp_file5 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            figs[4].savefig(temp_file5.name, dpi=100, bbox_inches='tight')
            pdf.image(temp_file5.name, x=50, w=110)

    # --- PÁGINA 4: INTELIGÊNCIA ARTIFICIAL ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "5. Parecer da Inteligencia Artificial", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", size=11)
    import streamlit as st
    texto = st.session_state.get("analise_texto", "Analise nao gerada.")
    pdf.multi_cell(0, 7, txt=texto)

    return pdf.output(dest='S').encode('latin-1')
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
    
    # --- PÁGINA 1: RESUMO E PRIMEIRO GRÁFICO ---
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "1. Resumo Executivo", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", size=11)
    # Cards de resumo
    total_val = df[numericas[0]].sum() if numericas else 0
    media_val = df[numericas[0]].mean() if numericas else 0
    
    pdf.cell(0, 8, f"Total de Registros Analisados: {len(df)}", ln=True)
    pdf.cell(0, 8, f"Volume Total Processado: {total_val:,.2f}", ln=True)
    pdf.cell(0, 8, f"Ticket Medio: {media_val:,.2f}", ln=True)
    pdf.ln(10)

    # Gráfico 1 (Ranking)
    if len(figs) > 0:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "2. Analise de Ranking (Top Performers)", ln=True)
        # Salva e insere
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        figs[0].savefig(temp_file.name, dpi=100, bbox_inches='tight')
        pdf.image(temp_file.name, x=10, w=190)
        pdf.ln(5)

    # --- PÁGINA 2: TENDÊNCIAS E COMPOSIÇÃO ---
    if len(figs) > 1:
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "3. Analise Temporal e Distribuicao", ln=True)
        pdf.ln(5)

        # Gráfico 2 (Linha do Tempo)
        temp_file2 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        figs[1].savefig(temp_file2.name, dpi=100, bbox_inches='tight')
        pdf.image(temp_file2.name, x=10, w=180) # Um pouco menor para caber dois
        pdf.ln(10)

        # Gráfico 3 (Pizza/Donut) se existir
        if len(figs) > 2:
            pdf.cell(0, 10, "Share de Mercado (Top 5 vs Outros)", ln=True)
            temp_file3 = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
            figs[2].savefig(temp_file3.name, dpi=100, bbox_inches='tight')
            pdf.image(temp_file3.name, x=30, w=150) # Centralizado

    # --- PÁGINA 3: INTELIGÊNCIA ARTIFICIAL ---
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "4. Parecer da Inteligencia Artificial", ln=True)
    pdf.ln(5)
    
    pdf.set_font("Arial", size=11)
    import streamlit as st
    texto = st.session_state.get("analise_texto", "Analise nao gerada.")
    pdf.multi_cell(0, 7, txt=texto)

    return pdf.output(dest='S').encode('latin-1')
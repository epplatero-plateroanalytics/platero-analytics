from fpdf import FPDF
import matplotlib.pyplot as plt
import os

class PDF(FPDF):
    def header(self):
        # --- 1. MARCA D'ÁGUA (Fica no fundo) ---
        # Define cor cinza bem claro
        self.set_text_color(245, 245, 245)  
        self.set_font('Arial', 'B', 50)
        # Coloca o texto centralizado na página
        # O '0' no w faz ocupar a largura toda, o align='C' centraliza
        self.set_xy(0, 100) # Posição vertical (meio da página mais ou menos)
        self.cell(0, 10, 'PLATERO ANALYTICS', align='C')
        
        # --- 2. LOGOTIPO ---
        # Verifica se o arquivo logo.png existe para não dar erro
        if os.path.exists('logo.png'):
            # (arquivo, x, y, largura)
            # Ajuste o 'w=30' se o logo ficar muito grande ou pequeno
            self.image('logo.png', 10, 8, w=30)

        # --- 3. TÍTULO DO CABEÇALHO ---
        self.set_y(15) # Move cursor para baixo do logo
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 0, 0) # Volta para cor preta
        # Título alinhado à direita para não bater no logo
        self.cell(0, 10, 'Relatorio Premium - Platero Analytics', 0, 1, 'R')
        self.ln(20) # Dá um espaço antes de começar o texto do relatório

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Platero Analytics - Pagina {self.page_no()}', 0, 0, 'C')

def gerar_pdf(df, df_filtrado, datas, numericas, categoricas, figs, lang="pt"):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # 1. Resumo Executivo
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. Resumo dos Dados", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, f"Total de Linhas Processadas: {len(df)}", ln=True)
    pdf.cell(0, 10, f"Colunas Numericas Identificadas: {len(numericas)}", ln=True)
    pdf.ln(5)
    
    # 2. Inserir Gráfico
    if figs:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, "2. Analise Visual", ln=True)
        
        # Salva o gráfico temporariamente
        figs[0].savefig("temp_chart.png", dpi=100, bbox_inches='tight')
        pdf.image("temp_chart.png", x=10, w=190)
        pdf.ln(5)
        
    # 3. Análise Escrita (automática)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "3. Insights Automaticos", ln=True)
    pdf.set_font("Arial", size=11)
    
    # Pega o texto gerado no layout ou usa um padrão
    import streamlit as st
    texto = st.session_state.get("analise_texto", "Analise padrao gerada pelo sistema.")
    pdf.multi_cell(0, 8, txt=texto)

    # Gera o binário do PDF
    return pdf.output(dest='S').encode('latin-1')
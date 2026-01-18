import streamlit as st
import pandas as pd
import io

# Importando seus módulos (Certifique-se que cleaner.py, utils.py etc. estão na pasta)
from cleaner import limpar_planilha
from utils import detectar_tipos
from layout import render_layout
from pdf_engine_cloud import gerar_pdf

st.set_page_config(
    page_title="Relatório Premium — Platero Analytics",
    layout="wide"
)

# Inicializa estado para o PDF não sumir
if "pdf_ready" not in st.session_state:
    st.session_state["pdf_ready"] = False

st.title("🚀 Agente Universal PRO — Platero Analytics")
st.markdown("---")

# --- BARRA LATERAL (Entrada) ---
st.sidebar.header("1. Upload de Arquivo")
arquivo = st.sidebar.file_uploader("Selecione sua planilha", type=["xlsx", "csv"])

# --- NOVO: Slider para corrigir o cabeçalho ---
if arquivo:
    st.sidebar.markdown("---")
    st.sidebar.header("2. Ajuste de Leitura")
    st.sidebar.info("Se os gráficos ficarem vazios, aumente este número para pular o título da planilha.")
    # O slider vai de 0 a 10 linhas
    pular_linhas = st.sidebar.slider("Pular linhas do topo:", 0, 10, 0)
else:
    pular_linhas = 0

if not arquivo:
    st.info("⬅️ Envie uma planilha na barra lateral para começar.")
    st.stop()

# --- LEITURA DO ARQUIVO COM O AJUSTE ---
try:
    if arquivo.name.endswith(".xlsx"):
        df = pd.read_excel(arquivo, skiprows=pular_linhas)
    else:
        try:
            df = pd.read_csv(arquivo, sep=";", skiprows=pular_linhas)
        except:
            df = pd.read_csv(arquivo, sep=",", skiprows=pular_linhas)
            
    # --- VISUALIZADOR DE DADOS (PARA VOCÊ CONFERIR) ---
    with st.expander("👀 Clique aqui para conferir se o Robô leu certo", expanded=True):
        st.write("Verifique se a primeira linha em negrito contém nomes como 'Data', 'Valor'. Se tiver o Título da empresa, aumente o slider ao lado!")
        st.dataframe(df.head())

except Exception as e:
    st.error(f"Erro ao ler o arquivo: {e}")
    st.stop()

if df.empty:
    st.error("A planilha está vazia ou você pulou linhas demais.")
    st.stop()

# --- PROCESSAMENTO MODULAR ---

# 1. Limpeza
df = limpar_planilha(df)

# 2. Detecção de Tipos
datas, numericas, categoricas = detectar_tipos(df)

# Verificação de segurança
if not numericas:
    st.warning("⚠️ Não encontramos colunas com números automaticamente.")
    st.write("Dica: Aumente o número de 'Pular linhas do topo' na barra lateral até que os números apareçam corretamente na tabela acima.")
    st.stop()

# 3. Renderizar Layout (Dashboard)
df_filtrado = render_layout(df, datas, numericas, categoricas, lang="pt")

# 4. Geração do PDF
if st.session_state.get("pdf_ready"):
    figs = st.session_state.get("figs_pdf", [])

    try:
        with st.spinner("Gerando PDF Premium..."):
            pdf_bytes = gerar_pdf(
                df=df,
                df_filtrado=df_filtrado,
                datas=datas,
                numericas=numericas,
                categoricas=categoricas,
                figs=figs,
                lang="pt"
            )

        st.success("PDF Premium gerado com sucesso!")

        st.download_button(
            "⬇️ Baixar Relatório Premium",
            data=pdf_bytes,
            file_name="relatorio_platero_premium.pdf",
            mime="application/pdf"
        )
        
        st.session_state["pdf_ready"] = False

    except Exception as e:
        st.error(f"Erro ao gerar PDF: {e}")
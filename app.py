import streamlit as st
import pandas as pd
from cleaner import limpar_planilha
from utils import detectar_tipos
from layout import render_layout
from pdf_engine_cloud import gerar_pdf
from ai_analyst import analisar_com_ia  # Importando a nova função

# --- Configuração da Página ---
st.set_page_config(
    page_title="Relatório Premium — Platero Analytics",
    layout="wide"
)

if "pdf_ready" not in st.session_state:
    st.session_state["pdf_ready"] = False
if "analise_ia" not in st.session_state:
    st.session_state["analise_ia"] = ""

st.title("🚀 Agente Universal PRO — Platero Analytics")
st.markdown("---")

# --- BARRA LATERAL ---
st.sidebar.header("1. Upload de Arquivo")
arquivo = st.sidebar.file_uploader("Selecione sua planilha", type=["xlsx", "csv"])

if arquivo:
    st.sidebar.markdown("---")
    st.sidebar.header("2. Ajuste de Leitura")
    pular_linhas = st.sidebar.slider("Pular linhas do topo:", 0, 10, 0)
else:
    pular_linhas = 0

if not arquivo:
    st.info("⬅️ Envie uma planilha na barra lateral para começar.")
    st.stop()

# --- LEITURA ---
try:
    if arquivo.name.endswith(".xlsx"):
        df = pd.read_excel(arquivo, skiprows=pular_linhas)
    else:
        try:
            df = pd.read_csv(arquivo, sep=";", skiprows=pular_linhas)
        except:
            df = pd.read_csv(arquivo, sep=",", skiprows=pular_linhas)

    with st.expander("👀 Clique para conferir a leitura", expanded=True):
        st.dataframe(df.head())

except Exception as e:
    st.error(f"Erro ao ler o arquivo: {e}")
    st.stop()

if df.empty:
    st.error("A planilha está vazia.")
    st.stop()

# --- PROCESSAMENTO ---
df = limpar_planilha(df)
datas, numericas, categoricas = detectar_tipos(df)

if not numericas:
    st.warning("⚠️ Não encontramos colunas numéricas.")
    st.stop()

# --- PAINEL INTERATIVO ---
st.subheader("📊 Painel de Controle")
col_grafico, col_insights = st.columns([2, 1])

with col_grafico:
    # Renderiza o gráfico e retorna os dados filtrados
    df_filtrado = render_layout(df, datas, numericas, categoricas, lang="pt")
    
    # Recupera as colunas que o usuário escolheu lá no layout.py (usando session_state seria melhor, mas vamos simplificar pegando do dataframe filtrado se possivel, ou assumindo que o layout define)
    # Para simplificar a integração com a IA, vamos adicionar seletores manuais aqui se necessário, 
    # mas o render_layout já faz isso. Vamos pegar o que foi gerado.

with col_insights:
    st.subheader("🤖 Inteligência Artificial")
    st.info("A IA vai ler os dados do gráfico e escrever o relatório para você.")
    
    # Identificar quais colunas estão sendo usadas (Isso é um truque para pegar o que o usuário escolheu no layout)
    # Na versão simples, vamos pedir para o usuário confirmar as colunas para a IA
    col_x_ia = st.selectbox("Coluna de Texto/Data para IA analisar:", list(df.columns), index=0)
    col_y_ia = st.selectbox("Coluna de Valor para IA analisar:", list(df.columns), index=len(df.columns)-1)

    if st.button("✨ Gerar Análise Automática"):
        with st.spinner("A IA está pensando..."):
            # Chama a função do arquivo novo
            texto_ia = analisar_com_ia(df, col_x_ia, col_y_ia)
            st.session_state["analise_ia"] = texto_ia
            
    # Área de texto editável (A IA preenche, mas você pode alterar)
    analise_final = st.text_area("Texto Final do Relatório:", value=st.session_state["analise_ia"], height=200)
    
    # Salva no estado para o PDF pegar
    st.session_state["analise_texto"] = analise_final

    if st.button("📄 Gerar PDF com Análise"):
        st.session_state["pdf_ready"] = True

# --- GERAÇÃO DO PDF ---
if st.session_state.get("pdf_ready"):
    figs = st.session_state.get("figs_pdf", [])
    try:
        with st.spinner("Gerando PDF..."):
            pdf_bytes = gerar_pdf(
                df=df,
                df_filtrado=df, # Passamos o df completo ou filtrado
                datas=datas,
                numericas=numericas,
                categoricas=categoricas,
                figs=figs,
                lang="pt"
            )
        st.success("Sucesso!")
        st.download_button("⬇️ Baixar PDF", data=pdf_bytes, file_name="Relatorio_IA.pdf", mime="application/pdf")
        st.session_state["pdf_ready"] = False
    except Exception as e:
        st.error(f"Erro no PDF: {e}")
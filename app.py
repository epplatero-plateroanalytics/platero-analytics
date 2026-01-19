import streamlit as st
import pandas as pd
from cleaner import limpar_planilha
from utils import detectar_tipos
from layout import render_layout
from pdf_engine_cloud import gerar_pdf
from ai_analyst import analisar_com_ia

# --- Configuração da Página (TEM QUE SER A PRIMEIRA LINHA) ---
# --- Configuração da Página (TEM QUE SER A PRIMEIRA LINHA) ---
st.set_page_config(
    page_title="Relatório Premium — Platero Analytics",
    page_icon="logo.png",  # <--- AQUI MUDAMOS PARA O SEU LOGO
    layout="wide"
)

# --- SISTEMA DE LOGIN (O PORTEIRO) ---
def check_password():
    """Retorna True se o usuário tiver a senha correta."""

    def password_entered():
        """Checa se a senha digitada bate com a do cofre."""
        if st.session_state["password"] == st.secrets["SENHA_ACESSO"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Não armazena a senha
        else:
            st.session_state["password_correct"] = False

    # Se a senha já estiver correta, retorna True
    if st.session_state.get("password_correct", False):
        return True

    # Se não, mostra a tela de login
    st.title("🔒 Área Restrita - Platero Analytics")
    st.text_input(
        "Digite a senha de acesso:", 
        type="password", 
        on_change=password_entered, 
        key="password"
    )
    
    if "password_correct" in st.session_state:
        st.error("😕 Senha incorreta. Tente novamente.")
        
    return False

# SE A SENHA NÃO ESTIVER CERTA, PARA TUDO AQUI.
if not check_password():
    st.stop()

# ---------------------------------------------------------
# DAQUI PARA BAIXO É O SEU APP NORMAL
# ---------------------------------------------------------

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
    df_filtrado = render_layout(df, datas, numericas, categoricas, lang="pt")

with col_insights:
    st.subheader("🤖 Inteligência Artificial")
    
    # SELETORES DA IA (CORRIGIDO: AGORA SÓ ACEITA NÚMEROS NO VALOR)
    col_x_ia = st.selectbox("Coluna de Texto/Data:", list(df.columns), index=0)
    
    # Aqui está a correção: usamos a lista 'numericas' em vez de todas as colunas
    if numericas:
        col_y_ia = st.selectbox("Coluna de Valor (R$):", numericas, index=0)
    else:
        st.error("Sem colunas numéricas para a IA analisar.")
        st.stop()

    if st.button("✨ Gerar Análise Automática"):
        with st.spinner("A IA está analisando os dados..."):
            texto_ia = analisar_com_ia(df, col_x_ia, col_y_ia)
            st.session_state["analise_ia"] = texto_ia
            
    analise_final = st.text_area("Texto do Relatório:", value=st.session_state["analise_ia"], height=200)
    st.session_state["analise_texto"] = analise_final

    if st.button("📄 Gerar PDF"):
        st.session_state["pdf_ready"] = True

# --- GERAÇÃO DO PDF ---
if st.session_state.get("pdf_ready"):
    figs = st.session_state.get("figs_pdf", [])
    try:
        with st.spinner("Gerando PDF..."):
            # Passamos o df completo e os metadados corretos
            pdf_bytes = gerar_pdf(
                df=df, 
                df_filtrado=df, 
                datas=datas, 
                numericas=numericas, 
                categoricas=categoricas, 
                figs=figs, 
                lang="pt"
            )
        st.success("Sucesso!")
        st.download_button("⬇️ Baixar PDF", data=pdf_bytes, file_name="Relatorio_Platero.pdf", mime="application/pdf")
        st.session_state["pdf_ready"] = False
    except Exception as e:
        st.error(f"Erro no PDF: {e}")
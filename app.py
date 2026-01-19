import streamlit as st
import pandas as pd
from cleaner import limpar_planilha
from utils import detectar_tipos
from layout import render_layout
from pdf_engine_cloud import gerar_pdf
from ai_analyst import analisar_com_ia
from database import init_db, salvar_registro, carregar_historico # <--- NOVO IMPORT

# --- Configuração da Página ---
st.set_page_config(
    page_title="Relatório Premium — Platero Analytics",
    page_icon="logo.png",
    layout="wide"
)

# --- INICIALIZA O BANCO DE DADOS ---
init_db()

# --- SISTEMA DE LOGIN (AGORA IDENTIFICA O USUÁRIO) ---
def check_password():
    """Retorna True se o login for sucesso e SALVA O NOME DO USUÁRIO."""

    def password_entered():
        if "passwords" in st.secrets:
            usuarios = st.secrets["passwords"]
            senha_digitada = st.session_state["password"]
            
            # Procura a senha no dicionário para achar o NOME do usuário
            usuario_encontrado = None
            for user, password in usuarios.items():
                if password == senha_digitada:
                    usuario_encontrado = user
                    break
            
            if usuario_encontrado:
                st.session_state["password_correct"] = True
                st.session_state["username"] = usuario_encontrado # <--- Salva quem entrou
                del st.session_state["password"]
            else:
                st.session_state["password_correct"] = False
        else:
            st.error("⚠️ Erro: Arquivo de senhas (Secrets) não configurado.")

    if st.session_state.get("password_correct", False):
        return True

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("### 🔒 Área Restrita")
        st.text_input("Digite sua Chave de Acesso:", type="password", on_change=password_entered, key="password")
        if "password_correct" in st.session_state:
            st.error("🚫 Acesso negado.")

    return False

if not check_password():
    st.stop()

# Pega o nome do usuário logado
usuario_atual = st.session_state.get("username", "desconhecido")

# ---------------------------------------------------------
# DAQUI PARA BAIXO É O APP COM BANCO DE DADOS
# ---------------------------------------------------------

if "pdf_ready" not in st.session_state:
    st.session_state["pdf_ready"] = False
if "analise_ia" not in st.session_state:
    st.session_state["analise_ia"] = ""

# --- CABEÇALHO ---
col_logo, col_titulo = st.columns([1, 10])
with col_logo: st.image("logo.png", use_column_width=True)
with col_titulo: 
    st.markdown("# Agente Universal PRO — Platero Analytics")
    st.caption(f"Logado como: **{usuario_atual}**") # Mostra quem está logado

st.markdown("---")

# --- BARRA LATERAL (UPLOAD) ---
st.sidebar.header("1. Upload de Arquivo")
arquivo = st.sidebar.file_uploader("Selecione sua planilha", type=["xlsx", "csv"])

# --- ÁREA DO HISTÓRICO (NOVIDADE!) ---
st.sidebar.markdown("---")
st.sidebar.header("📜 Histórico de Envios")
if st.sidebar.checkbox("Ver meu histórico"):
    df_hist = carregar_historico(usuario_atual)
    if not df_hist.empty:
        st.sidebar.dataframe(df_hist)
        st.sidebar.info(f"Você já processou {len(df_hist)} relatórios.")
    else:
        st.sidebar.warning("Nenhum histórico encontrado.")

if not arquivo:
    st.info("⬅️ Envie uma planilha na barra lateral para começar.")
    st.stop()

# --- LEITURA ---
try:
    if arquivo.name.endswith(".xlsx"):
        df = pd.read_excel(arquivo)
    else:
        df = pd.read_csv(arquivo, sep=",") # Tenta vírgula padrão

    with st.expander("👀 Clique para conferir a leitura", expanded=False):
        st.dataframe(df.head())

except Exception as e:
    st.error(f"Erro ao ler: {e}")
    st.stop()

# --- PROCESSAMENTO ---
df = limpar_planilha(df)
datas, numericas, categoricas = detectar_tipos(df)

if not numericas:
    st.warning("⚠️ Não encontramos colunas numéricas.")
    st.stop()

# --- SALVAMENTO AUTOMÁTICO NO BANCO ---
# Verifica se já salvamos esse arquivo nesta sessão para não duplicar
chave_salvamento = f"salvo_{arquivo.name}"
if chave_salvamento not in st.session_state:
    sucesso = salvar_registro(usuario_atual, arquivo.name, df, numericas[0])
    if sucesso:
        st.toast("✅ Dados salvos no histórico com sucesso!")
        st.session_state[chave_salvamento] = True

# --- PAINEL INTERATIVO ---
st.subheader("📊 Painel de Controle")
col_grafico, col_insights = st.columns([2, 1])

with col_grafico:
    df_filtrado = render_layout(df, datas, numericas, categoricas, lang="pt")

with col_insights:
    st.subheader("🤖 Inteligência Artificial")
    col_x_ia = st.selectbox("Eixo X (Texto):", list(df.columns), index=0)
    col_y_ia = st.selectbox("Eixo Y (Valor):", numericas, index=0)

    if st.button("✨ Gerar Análise"):
        with st.spinner("Analisando..."):
            texto_ia = analisar_com_ia(df, col_x_ia, col_y_ia)
            st.session_state["analise_ia"] = texto_ia
            
    analise_final = st.text_area("Relatório:", value=st.session_state["analise_ia"], height=200)
    st.session_state["analise_texto"] = analise_final

    if st.button("📄 Gerar PDF"):
        st.session_state["pdf_ready"] = True

# --- GERAÇÃO DO PDF ---
if st.session_state.get("pdf_ready"):
    figs = st.session_state.get("figs_pdf", [])
    pdf_bytes = gerar_pdf(df, df, datas, numericas, categoricas, figs, lang="pt")
    st.download_button("⬇️ Baixar PDF", data=pdf_bytes, file_name="Relatorio_Platero.pdf", mime="application/pdf")
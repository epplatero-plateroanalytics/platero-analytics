import streamlit as st
import pandas as pd
from cleaner import limpar_planilha
from utils import detectar_tipos
from layout import render_layout
from pdf_engine_cloud import gerar_pdf
from ai_analyst import analisar_com_ia
from database import init_db, salvar_registro, carregar_historico

# --- Configuração da Página ---
st.set_page_config(
    page_title="Relatório Premium — Platero Analytics",
    page_icon="logo.png",
    layout="wide"
)

# --- INICIALIZA O BANCO DE DADOS ---
init_db()

# --- SISTEMA DE LOGIN ---
def check_password():
    """Retorna True se o login for sucesso e SALVA O NOME DO USUÁRIO."""
    def password_entered():
        if "passwords" in st.secrets:
            usuarios = st.secrets["passwords"]
            senha_digitada = st.session_state["password"]
            
            # Procura a senha no dicionário
            usuario_encontrado = None
            for user, password in usuarios.items():
                if password == senha_digitada:
                    usuario_encontrado = user
                    break
            
            if usuario_encontrado:
                st.session_state["password_correct"] = True
                st.session_state["username"] = usuario_encontrado
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

# Pega o usuário logado
usuario_atual = st.session_state.get("username", "desconhecido")

# ---------------------------------------------------------
# DAQUI PARA BAIXO É O APP PRINCIPAL
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
    st.caption(f"Logado como: **{usuario_atual}**")

st.markdown("---")

# --- BARRA LATERAL ---
st.sidebar.header("1. Upload de Arquivo")
arquivo = st.sidebar.file_uploader("Selecione sua planilha", type=["xlsx", "csv"])

st.sidebar.markdown("---")
st.sidebar.header("📜 Histórico de Envios")
if st.sidebar.checkbox("Ver meu histórico"):
    df_hist = carregar_historico(usuario_atual)
    if not df_hist.empty:
        st.sidebar.dataframe(df_hist)
    else:
        st.sidebar.warning("Nenhum histórico encontrado.")

if arquivo:
    st.sidebar.markdown("---")
    st.sidebar.header("2. Ajuste de Leitura")
    # Já deixei o padrão em 2 para facilitar sua vida com as planilhas atuais
    pular_linhas = st.sidebar.slider("Pular linhas do topo:", 0, 10, 2)
else:
    pular_linhas = 2

if not arquivo:
    st.info("⬅️ Envie uma planilha na barra lateral para começar.")
    st.stop()

# --- LEITURA INTELIGENTE (MULTI-ABAS) ---
try:
    if arquivo.name.endswith(".xlsx"):
        # Lê TODAS as abas de uma vez
        dfs_dict = pd.read_excel(arquivo, sheet_name=None, skiprows=pular_linhas)
        
        lista_dfs = []
        for nome_aba, df_aba in dfs_dict.items():
            # Cria coluna para identificar o ano/aba
            df_aba["Origem_Aba"] = nome_aba 
            lista_dfs.append(df_aba)
        
        # Junta tudo numa tabela só
        df = pd.concat(lista_dfs, ignore_index=True)

    else:
        # Se for CSV
        try:
            df = pd.read_csv(arquivo, sep=";", skiprows=pular_linhas)
        except:
            df = pd.read_csv(arquivo, sep=",", skiprows=pular_linhas)

    with st.expander("👀 Clique para conferir a leitura (Dados Unificados)", expanded=False):
        if arquivo.name.endswith(".xlsx"):
            st.info(f"Abas processadas: {list(dfs_dict.keys())}")
        st.dataframe(df.head())
        st.write(f"Total de linhas importadas: {len(df)}")

except Exception as e:
    st.error(f"Erro ao ler o arquivo: {e}")
    st.stop()

if df.empty:
    st.error("A planilha está vazia.")
    st.stop()

# --- PROCESSAMENTO E LIMPEZA ---
df = limpar_planilha(df)
datas, numericas, categoricas = detectar_tipos(df)

if not numericas:
    st.warning("⚠️ Não encontramos colunas numéricas.")
    st.stop()

# --- SALVAMENTO NO BANCO ---
chave_salvamento = f"salvo_{arquivo.name}_{len(df)}"
if chave_salvamento not in st.session_state:
    salvar_registro(usuario_atual, arquivo.name, df, numericas[0])
    st.toast("✅ Dados salvos no histórico!")
    st.session_state[chave_salvamento] = True

# --- PAINEL INTERATIVO ---
st.subheader("📊 Painel de Controle")
col_grafico, col_insights = st.columns([2, 1])

with col_grafico:
    # Renderiza os gráficos e guarda na sessão para o PDF
    df_filtrado = render_layout(df, datas, numericas, categoricas, lang="pt")

with col_insights:
    st.subheader("🤖 Inteligência Artificial")
    
    # Seletor inteligente de colunas
    opcoes_x = list(df.columns)
    idx_x = 0
    # Tenta achar a coluna de "Cliente" ou "Nome" automaticamente
    for i, col in enumerate(opcoes_x):
        if "CLIENTE" in str(col).upper() or "NOME" in str(col).upper():
            idx_x = i
            break
            
    col_x_ia = st.
import streamlit as st
import pandas as pd
from cleaner import carregar_e_limpar_inteligente # <--- NOVA FUNÇÃO
from utils import detectar_tipos
from layout import render_layout
from pdf_engine_cloud import gerar_pdf
from ai_analyst import analisar_com_ia
from database import init_db, salvar_registro, carregar_historico

st.set_page_config(page_title="Platero Analytics PRO", page_icon="📊", layout="wide")
init_db()

# --- CSS PARA VISUAL PROFISSIONAL ---
st.markdown("""
<style>
    .metric-card {background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center;}
    div[data-testid="stExpander"] {border: none; box-shadow: 0px 2px 5px rgba(0,0,0,0.1);}
</style>
""", unsafe_allow_html=True)

# --- LOGIN (MANTIDO IGUAL) ---
def check_password():
    if st.session_state.get("password_correct", False): return True
    def password_entered():
        if "passwords" in st.secrets and st.session_state["password"] in st.secrets["passwords"].values():
            st.session_state["password_correct"] = True
            st.session_state["username"] = [k for k,v in st.secrets["passwords"].items() if v==st.session_state["password"]][0]
            del st.session_state["password"]
        else: st.session_state["password_correct"] = False

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.markdown("### 🔒 Acesso Corporativo")
        st.text_input("Chave de Acesso:", type="password", on_change=password_entered, key="password")
        if "password_correct" in st.session_state: st.error("Chave inválida.")
    return False

if not check_password(): st.stop()
usuario_atual = st.session_state.get("username", "Cliente")

# --- APP PRINCIPAL ---
col_logo, col_titulo = st.columns([1, 6])
with col_titulo:
    st.title(f"Painel Executivo — {usuario_atual.title()}")
st.markdown("---")

# --- SIDEBAR ---
with st.sidebar:
    st.header("📂 Central de Arquivos")
    arquivo = st.file_uploader("Carregar Base de Dados (Excel/CSV)", type=["xlsx", "csv"])
    
    st.markdown("---")
    if st.checkbox("Ver Histórico de Processamento"):
        st.dataframe(carregar_historico(usuario_atual))

if not arquivo:
    st.info("👋 Bem-vindo! Arraste sua planilha para começar a análise automática.")
    st.stop()

# --- CARREGAMENTO INTELIGENTE (O SEGREDO) ---
with st.spinner("🔄 O Motor Platero está analisando a estrutura do arquivo..."):
    # Chama a nova função do cleaner.py
    df, erro = carregar_e_limpar_inteligente(arquivo)

if erro:
    st.error(f"Não conseguimos processar este arquivo: {erro}")
    st.stop()

if df.empty:
    st.warning("O arquivo parece vazio ou não contém dados legíveis.")
    st.stop()

# Detecta tipos automaticamente
datas, numericas, categoricas = detectar_tipos(df)

if not numericas:
    st.error("⚠️ Identificamos os dados, mas não achamos colunas de VALOR (Dinheiro/Quantidade). Verifique se a planilha tem números.")
    st.stop()

# --- DASHBOARD EXECUTIVO (VISUAL MELHORADO) ---

# 1. KPIs (Indicadores Principais)
st.subheader("📈 Visão Geral")
col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

valor_total = df[numericas[0]].sum()
media_valor = df[numericas[0]].mean()
total_linhas = len(df)

with col_kpi1: st.metric("Faturamento Total / Volume", f"R$ {valor_total:,.2f}")
with col_kpi2: st.metric("Ticket Médio", f"R$ {media_valor:,.2f}")
with col_kpi3: st.metric("Registros Processados", f"{total_linhas}")

st.markdown("---")

# 2. ÁREA DE GRÁFICOS
col_grafico, col_config = st.columns([3, 1])

with col_config:
    st.markdown("### ⚙️ Ajuste Fino")
    
    # Tenta sugerir o Eixo X inteligentemente
    index_padrao = 0
    if "Origem_Aba" in df.columns: # Se tiver abas (anos), sugere usar elas
        try: index_padrao = list(df.columns).index("Origem_Aba")
        except: pass
    elif datas: # Se não, sugere a Data
        try: index_padrao = list(df.columns).index(datas[0])
        except: pass
        
    eixo_x_view = st.selectbox("Agrupar Dados Por:", list(df.columns), index=index_padrao)
    eixo_y_view = st.selectbox("Métrica Analisada:", numericas, index=0)
    
    # Checkbox para salvar
    chave_salvo = f"save_{arquivo.name}_{len(df)}"
    if chave_salvo not in st.session_state:
        salvar_registro(usuario_atual, arquivo.name, df, eixo_y_view)
        st.session_state[chave_salvo] = True

with col_grafico:
    # Chama o renderizador visual
    df_agrupado = render_layout(df, datas, numericas, categoricas, lang="pt")

# 3. INTELIGÊNCIA ARTIFICIAL
st.markdown("---")
st.subheader("🤖 Consultor Virtual")
col_ia_txt, col_ia_btn = st.columns([4, 1])

with col_ia_btn:
    if st.button("✨ Analisar com IA", type="primary"):
        with st.spinner("Lendo padrões e redigindo relatório..."):
            analise = analisar_com_ia(df, eixo_x_view, eixo_y_view)
            st.session_state["analise_ia"] = analise

if "analise_ia" in st.session_state:
    st.info(st.session_state["analise_ia"])

# 4. EXPORTAÇÃO
if st.button("📄 Baixar Relatório PDF Completo"):
    figs = st.session_state.get("figs_pdf", [])
    pdf_bytes = gerar_pdf(df, df, datas, numericas, categoricas, figs, lang="pt")
    st.download_button("⬇️ Download PDF", pdf_bytes, "Relatorio_Platero_Pro.pdf", "application/pdf")
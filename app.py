import streamlit as st
import pandas as pd
import io

# Importações locais - Certifique-se que estes arquivos existem na mesma pasta
from cleaner import carregar_e_limpar_inteligente
from utils import detectar_tipos
from layout import render_layout
from pdf_engine_cloud import gerar_pdf_pro
from ai_analyst import analisar_com_ia
from database import init_db, salvar_registro, carregar_historico

# ============================================================
# CONFIGURAÇÃO INICIAL
# ============================================================

st.set_page_config(page_title="Platero Analytics PRO", page_icon="📊", layout="wide")
try:
    init_db()
except:
    pass # Ignora erro de DB se não estiver configurado localmente

st.markdown("""
<style>
    .metric-card {background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center;}
    div[data-testid="stExpander"] {border: none; box-shadow: 0px 2px 5px rgba(0,0,0,0.1);}
</style>
""", unsafe_allow_html=True)

# ============================================================
# LOGIN
# ============================================================

def check_password():
    if st.session_state.get("password_correct", False):
        return True

    def password_entered():
        if "passwords" in st.secrets and st.session_state["password"] in st.secrets["passwords"].values():
            st.session_state["password_correct"] = True
            st.session_state["username"] = [
                k for k, v in st.secrets["passwords"].items() if v == st.session_state["password"]
            ][0]
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    # Se não houver secrets configurados, libera acesso direto (para testes locais)
    if "passwords" not in st.secrets:
        return True

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🔒 Acesso Corporativo")
        st.text_input("Chave de Acesso:", type="password", on_change=password_entered, key="password")
        if "password_correct" in st.session_state:
            st.error("Chave inválida.")

    return False

if not check_password():
    st.stop()

usuario_atual = st.session_state.get("username", "Cliente")

# ============================================================
# CABEÇALHO
# ============================================================

col_logo, col_titulo = st.columns([1, 6])
with col_titulo:
    st.title(f"Painel Executivo — {usuario_atual.title()}")

st.markdown("---")

# ============================================================
# SIDEBAR & CARREGAMENTO
# ============================================================

with st.sidebar:
    st.header("📂 Central de Arquivos")
    arquivo = st.file_uploader("Carregar Base de Dados (Excel/CSV)", type=["xlsx", "csv"])
    
    usar_modo_seguro = st.checkbox("🛠️ Modo Seguro (Carregamento Simples)", 
                                  help="Marque se os números aparecerem gigantes ou errados.")

    st.markdown("---")
    if st.checkbox("Ver Histórico de Processamento"):
        try:
            st.dataframe(carregar_historico(usuario_atual))
        except:
            st.info("Histórico indisponível.")

if not arquivo:
    st.info("👋 Bem-vindo! Arraste sua planilha para começar a análise automática.")
    st.stop()

# ============================================================
# LÓGICA DE CARREGAMENTO
# ============================================================

df = pd.DataFrame()
erro = None

with st.spinner("🔄 Processando arquivo..."):
    if usar_modo_seguro:
        try:
            if arquivo.name.endswith('.csv'):
                try:
                    df = pd.read_csv(arquivo, sep=None, engine='python')
                except:
                    arquivo.seek(0)
                    df = pd.read_csv(arquivo, sep=',')
            else:
                df = pd.read_excel(arquivo)
            df = df.convert_dtypes()
        except Exception as e:
            erro = f"Erro no modo seguro: {e}"
    else:
        df, erro = carregar_e_limpar_inteligente(arquivo)

if erro:
    st.error(f"Não conseguimos processar este arquivo: {erro}")
    st.stop()

if df.empty:
    st.warning("O arquivo parece vazio ou não contém dados legíveis.")
    st.stop()

# ============================================================
# DETECÇÃO DE TIPOS
# ============================================================

tipos = detectar_tipos(df)

datas = tipos["datas"]
numericas = tipos["numericas"]
categoricas = tipos["categoricas"]
monetarias = tipos["monetarias"]
quantidades = tipos["quantidades"]
booleanas = tipos["booleanas"]
texto_livre = tipos["texto_livre"]

if not numericas:
    st.error("⚠️ Identificamos os dados, mas não achamos colunas numéricas.")
    st.stop()

# ============================================================
# KPIs PRINCIPAIS
# ============================================================

st.subheader("📈 Visão Geral")

col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

col_kpi_padrao = numericas[0]
valor_total = df[col_kpi_padrao].sum()
media_valor = df[col_kpi_padrao].mean()
total_linhas = len(df)

with col_kpi1:
    st.metric("Total Geral", f"{valor_total:,.2f}")

with col_kpi2:
    st.metric("Média Geral", f"{media_valor:,.2f}")

with col_kpi3:
    st.metric("Registros Processados", f"{total_linhas}")

st.markdown("---")

# ============================================================
# ÁREA DE GRÁFICOS
# ============================================================

col_grafico, col_config = st.columns([3, 1])

with col_config:
    st.markdown("### ⚙️ Ajuste Fino")

    index_padrao = 0
    if "Origem_Aba" in df.columns:
        index_padrao = list(df.columns).index("Origem_Aba")
    elif datas:
        index_padrao = list(df.columns).index(datas[0])

    eixo_x_view = st.selectbox("Agrupar Dados Por:", list(df.columns), index=index_padrao)
    eixo_y_view = st.selectbox("Métrica Analisada:", numericas, index=0)

    chave_salvo = f"save_{arquivo.name}_{len(df)}"
    if chave_salvo not in st.session_state:
        try:
            salvar_registro(usuario_atual, arquivo.name, df, eixo_y_view)
        except:
            pass
        st.session_state[chave_salvo] = True

with col_grafico:
    df_agrupado = render_layout(df, datas, numericas, categoricas, lang="pt")

# ============================================================
# CONSULTOR VIRTUAL
# ============================================================

st.markdown("---")
st.subheader("🤖 Consultor Virtual — Análise Avançada")

col_ia_txt, col_ia_btn = st.columns([4, 1])

with col_ia_btn:
    if st.button("✨ Analisar com IA Premium", type="primary"):
        with st.spinner("Lendo padrões..."):
            analise = analisar_com_ia(df, eixo_x_view, eixo_y_view)
            st.session_state["analise_ia"] = analise

if "analise_ia" in st.session_state:
    st.info(st.session_state["analise_ia"])

# ============================================================
# EXPORTAÇÃO DO RELATÓRIO
# ============================================================

st.markdown("---")
st.subheader("📄 Exportação do Relatório")

with st.container():
    st.markdown("""
    <div style="background-color: #f8f9fc; padding: 25px; border-radius: 12px; border: 1px solid #e0e0e0;">
        <h3 style="margin-top: 0; color: #003366;">📘 Relatório Executivo Profissional</h3>
        <p style="font-size: 15px; color: #444;">Gere um relatório completo em PDF.</p>
    </div>
    """, unsafe_allow_html=True)

    st.write("")
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

    if "pdf_bytes" not in st.session_state:
        st.session_state["pdf_bytes"] = None

    with col_btn2:
        if st.button("📄 Gerar Relatório PDF", type="primary"):
            figs = st.session_state.get("figs_pdf", [])
            texto_ia = st.session_state.get("analise_ia", "")

            with st.spinner("📑 Montando relatório..."):
                try:
                    pdf_data = gerar_pdf_pro(
                        df_original=df,
                        df_limpo=df,
                        datas=datas,
                        numericas=numericas,
                        categoricas=categoricas,
                        figs_principais=figs,
                        texto_ia=texto_ia,
                        usuario=usuario_atual,
                        coluna_alvo=eixo_y_view
                    )
                    st.session_state["pdf_bytes"] = bytes(pdf_data)
                    st.success("Relatório gerado!")
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {e}")

        if st.session_state["pdf_bytes"] is not None:
            st.download_button(
                label="⬇️ Baixar Relatório PDF",
                data=st.session_state["pdf_bytes"],
                file_name="Relatorio_Platero_Pro.pdf",
                mime="application/pdf",
                type="primary"
            )
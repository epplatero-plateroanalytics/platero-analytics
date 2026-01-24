import streamlit as st
import pandas as pd
import io
import re

# Importações locais
from cleaner import carregar_e_limpar_inteligente
from utils import detectar_tipos
from layout import render_layout
from pdf_engine_cloud import gerar_pdf_pro
from ai_analyst import analisar_com_ia
from database import init_db, salvar_registro, carregar_historico

# ============================================================
# FUNÇÃO DE LIMPEZA FORÇADA DE NÚMEROS
# ============================================================
def limpar_coluna_numerica(serie):
    """
    Tenta converter uma coluna de texto/bagunçada para números decimais corretos.
    Lida com R$, pontos de milhar e vírgulas decimais.
    """
    # 1. Se já for número, devolve como está (mas verifica se não é gigante)
    if pd.api.types.is_numeric_dtype(serie):
        # Correção de segurança para leituras erradas (ex: 10^11 vezes maior)
        mediana = serie.median()
        if median > 1e14: # Se mediana > 100 Trilhões
             return serie / 1e11 # Tenta ajustar escala (heurística)
        return serie

    # 2. Converte para string e limpa
    serie_clean = serie.astype(str).str.strip()
    
    # Remove símbolos de moeda e espaços
    serie_clean = serie_clean.str.replace(r'[R$\s]', '', regex=True)

    def converter_valor(val):
        if not val or val.lower() == 'nan' or val == 'None':
            return None
            
        # Remove caracteres que não sejam números, ponto ou vírgula
        val = re.sub(r'[^\d.,-]', '', val)
        
        # Lógica para decidir Decimal vs Milhar
        if ',' in val and '.' in val:
            # Caso Brasileiro (1.234,56) -> Tira ponto, troca vírgula por ponto
            val = val.replace('.', '').replace(',', '.')
        elif ',' in val:
            # Caso apenas vírgula (1234,56) -> Troca por ponto
            val = val.replace(',', '.')
        # Caso apenas ponto (1234.56) -> Mantém
        
        try:
            return float(val)
        except:
            return None

    return serie_clean.apply(converter_valor)

# ============================================================
# CONFIGURAÇÃO INICIAL
# ============================================================

st.set_page_config(page_title="Platero Analytics PRO", page_icon="📊", layout="wide")
try:
    init_db()
except:
    pass 

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
    
    usar_modo_seguro = st.checkbox("🛠️ Modo Seguro (Limpeza Forçada)", 
                                  value=True,
                                  help="Ative se os números estiverem gigantes ou errados.")

    st.markdown("---")
    if st.checkbox("Ver Histórico"):
        try:
            st.dataframe(carregar_historico(usuario_atual))
        except:
            st.info("Histórico indisponível.")

if not arquivo:
    st.info("👋 Bem-vindo! Arraste sua planilha para começar a análise automática.")
    st.stop()

# ============================================================
# LÓGICA DE CARREGAMENTO (ROBUSTA)
# ============================================================

df = pd.DataFrame()
erro = None

with st.spinner("🔄 Processando arquivo..."):
    if usar_modo_seguro:
        try:
            # Lê TUDO como texto (dtype=str) para evitar conversão errada automática
            if arquivo.name.endswith('.csv'):
                try:
                    df = pd.read_csv(arquivo, sep=None, engine='python', dtype=str)
                except:
                    arquivo.seek(0)
                    df = pd.read_csv(arquivo, sep=',', dtype=str)
            else:
                df = pd.read_excel(arquivo, dtype=str)
            
            # Tenta converter colunas que parecem números
            for col in df.columns:
                # Pega amostra para ver se tem cara de número
                amostra = df[col].dropna().head(10).astype(str).str.cat()
                if any(char.isdigit() for char in amostra):
                    # Tenta converter
                    col_convertida = limpar_coluna_numerica(df[col])
                    # Se mais da metade virou número válido, aceita a conversão
                    if col_convertida.notna().sum() > (len(df) * 0.5):
                        df[col] = col_convertida

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
datas, numericas = tipos["datas"], tipos["numericas"]
categoricas = tipos["categoricas"]

if not numericas:
    st.error("⚠️ Identificamos os dados, mas não achamos colunas numéricas.")
    st.stop()

# ============================================================
# KPIs PRINCIPAIS
# ============================================================

st.subheader("📈 Visão Geral")

col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

# Garante KPI padrão seguro
col_kpi_padrao = numericas[0]
if "VENDAS" in numericas: col_kpi_padrao = "VENDAS" # Preferência inteligente

valor_total = df[col_kpi_padrao].sum()
media_valor = df[col_kpi_padrao].mean()
total_linhas = len(df)

with col_kpi1:
    st.metric(f"Total ({col_kpi_padrao})", f"{valor_total:,.2f}")

with col_kpi2:
    st.metric("Média", f"{media_valor:,.2f}")

with col_kpi3:
    st.metric("Registros", f"{total_linhas}")

st.markdown("---")

# ============================================================
# ÁREA DE GRÁFICOS
# ============================================================

col_grafico, col_config = st.columns([3, 1])

with col_config:
    st.markdown("### ⚙️ Ajuste Fino")

    index_padrao = 0
    if datas: index_padrao = list(df.columns).index(datas[0])
    elif "ANO" in df.columns: index_padrao = list(df.columns).index("ANO")

    eixo_x_view = st.selectbox("Agrupar Dados Por:", list(df.columns), index=index_padrao)
    
    # Seleção inteligente do índice numérico
    idx_num = 0
    if "VENDAS" in numericas: idx_num = numericas.index("VENDAS")
    eixo_y_view = st.selectbox("Métrica Analisada:", numericas, index=idx_num)

    chave_salvo = f"save_{arquivo.name}_{len(df)}"
    if chave_salvo not in st.session_state:
        try: salvar_registro(usuario_atual, arquivo.name, df, eixo_y_view)
        except: pass
        st.session_state[chave_salvo] = True

with col_grafico:
    df_agrupado = render_layout(df, datas, numericas, categoricas, lang="pt")

# ============================================================
# CONSULTOR VIRTUAL
# ============================================================

st.markdown("---")
st.subheader("🤖 Consultor Virtual")

col_ia_txt, col_ia_btn = st.columns([4, 1])

with col_ia_btn:
    if st.button("✨ Analisar com IA", type="primary"):
        with st.spinner("Analisando..."):
            analise = analisar_com_ia(df, eixo_x_view, eixo_y_view)
            st.session_state["analise_ia"] = analise

if "analise_ia" in st.session_state:
    st.info(st.session_state["analise_ia"])

# ============================================================
# EXPORTAÇÃO
# ============================================================

st.markdown("---")
st.subheader("📄 Exportação")

col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

if "pdf_bytes" not in st.session_state:
    st.session_state["pdf_bytes"] = None

with col_btn2:
    if st.button("📄 Gerar Relatório PDF", type="primary"):
        figs = st.session_state.get("figs_pdf", [])
        texto_ia = st.session_state.get("analise_ia", "")

        with st.spinner("Gerando PDF..."):
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
                st.success("Sucesso! Baixe abaixo.")
            except Exception as e:
                st.error(f"Erro no PDF: {e}")

    if st.session_state["pdf_bytes"] is not None:
        st.download_button(
            "⬇️ Baixar PDF",
            st.session_state["pdf_bytes"],
            "Relatorio_Platero_Pro.pdf",
            "application/pdf",
            type="primary"
        )
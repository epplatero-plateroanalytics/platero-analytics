import streamlit as st
import pandas as pd
import io
import re

# Importações locais (Mantenha seus arquivos auxiliares na mesma pasta)
from cleaner import carregar_e_limpar_inteligente
from utils import detectar_tipos
from layout import render_layout
from pdf_engine_cloud import gerar_pdf_pro
from ai_analyst import analisar_com_ia
from database import init_db, salvar_registro, carregar_historico

# ============================================================
# FUNÇÃO: LIMPEZA FORÇADA DE NÚMEROS
# ============================================================
def limpar_coluna_numerica(serie):
    """
    Converte qualquer bagunça (R$, texto, erro de ponto/vírgula) em número real.
    """
    if pd.api.types.is_numeric_dtype(serie):
        return serie

    serie_clean = serie.astype(str).str.strip()
    serie_clean = serie_clean.str.replace(r'[R$\s]', '', regex=True)

    def converter_valor(val):
        if not val or val.lower() in ['nan', 'none', '', 'null']:
            return None
        
        # Deixa apenas números, ponto, vírgula e sinal negativo
        val_clean = re.sub(r'[^\d.,-]', '', val)
        
        try:
            # Lógica Híbrida (Brasil vs EUA)
            if ',' in val_clean and '.' in val_clean:
                # 1.234,56 -> Tira ponto, troca vírgula por ponto
                val_clean = val_clean.replace('.', '').replace(',', '.')
            elif ',' in val_clean:
                # 1234,56 -> Troca vírgula por ponto
                val_clean = val_clean.replace(',', '.')
            
            return float(val_clean)
        except:
            return None

    return serie_clean.apply(converter_valor)

# ============================================================
# FUNÇÃO: GERAR MODELO PADRÃO
# ============================================================
@st.cache_data
def gerar_modelo_csv():
    df_modelo = pd.DataFrame({
        "DATA": ["01/01/2024", "02/01/2024", "03/01/2024"],
        "CATEGORIA": ["Serviços", "Produtos", "Serviços"],
        "PRODUTO": ["Consultoria", "Licença Software", "Manutenção"],
        "VENDAS": [1500.00, 2500.50, 800.00],
        "QUANTIDADE": [1, 5, 2]
    })
    return df_modelo.to_csv(index=False, sep=";").encode('latin-1') # Encoding Excel-Friendly

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
# SIDEBAR
# ============================================================

with st.sidebar:
    st.header("📂 Central de Arquivos")
    
    st.download_button(
        label="⬇️ Baixar Planilha Modelo",
        data=gerar_modelo_csv(),
        file_name="modelo_padrao_platero.csv",
        mime="text/csv",
        key="btn_download_modelo"
    )
    
    st.markdown("---")
    
    arquivo = st.file_uploader("Carregar Base de Dados", type=["xlsx", "csv"], key="uploader_principal")
    
    usar_modo_seguro = st.checkbox("🛠️ Modo Seguro (Limpeza Forçada)", 
                                  value=True,
                                  help="Ative para corrigir erros de leitura e números.",
                                  key="chk_modo_seguro")

    st.markdown("---")
    if st.checkbox("Ver Histórico", key="chk_historico"):
        try:
            st.dataframe(carregar_historico(usuario_atual))
        except:
            st.info("Histórico indisponível.")

if not arquivo:
    st.info("👋 Bem-vindo! Se tiver problemas, use a **Planilha Modelo**.")
    st.stop()

# ============================================================
# LÓGICA DE CARREGAMENTO BLINDADA (Corrige erro utf-8/0xe7)
# ============================================================

df = pd.DataFrame()
erro = None

with st.spinner("🔄 Processando arquivo..."):
    if usar_modo_seguro:
        try:
            # --- BLOCAGEM DE CODIFICAÇÃO (CORREÇÃO DO ERRO) ---
            if arquivo.name.endswith('.csv'):
                try:
                    # Tentativa 1: Padrão UTF-8 (Mundial)
                    df = pd.read_csv(arquivo, sep=None, engine='python', dtype=str)
                except UnicodeDecodeError:
                    # Tentativa 2: Latin-1 (Excel Brasil - corrige o erro do 'ç')
                    arquivo.seek(0)
                    df = pd.read_csv(arquivo, sep=None, engine='python', dtype=str, encoding='latin-1')
                except Exception:
                    # Tentativa 3: Força separador ; e Latin-1
                    arquivo.seek(0)
                    df = pd.read_csv(arquivo, sep=';', dtype=str, encoding='latin-1')
            else:
                # Excel (xlsx) não costuma ter problema de encoding
                df = pd.read_excel(arquivo, dtype=str)
            
            # --- CONVERSÃO INTELIGENTE DE NÚMEROS ---
            for col in df.columns:
                amostra = df[col].dropna().head(10).astype(str).str.cat()
                # Se tem números na amostra, tenta limpar
                if any(char.isdigit() for char in amostra):
                    col_convertida = limpar_coluna_numerica(df[col])
                    # Se converteu bem, salva
                    if col_convertida.notna().sum() > (len(df) * 0.5):
                        df[col] = col_convertida

        except Exception as e:
            erro = f"Erro grave no modo seguro: {e}"
    else:
        df, erro = carregar_e_limpar_inteligente(arquivo)

if erro:
    st.error(f"Não foi possível ler o arquivo: {erro}")
    st.stop()

if df.empty:
    st.warning("O arquivo parece vazio.")
    st.stop()

# ============================================================
# DETECÇÃO DE TIPOS
# ============================================================

tipos = detectar_tipos(df)
datas, numericas = tipos["datas"], tipos["numericas"]
categoricas = tipos["categoricas"]

if not numericas:
    st.error("⚠️ Não encontramos colunas numéricas (Vendas, Valor, etc).")
    st.stop()

# ============================================================
# KPIs
# ============================================================

st.subheader("📈 Visão Geral")

col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

col_kpi_padrao = numericas[0]
for col in numericas:
    if "VENDA" in col.upper() or "VALOR" in col.upper() or "TOTAL" in col.upper():
        col_kpi_padrao = col
        break

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
# GRÁFICOS
# ============================================================

col_grafico, col_config = st.columns([3, 1])

with col_config:
    st.markdown("### ⚙️ Ajuste Fino")

    index_padrao = 0
    if datas: index_padrao = list(df.columns).index(datas[0])
    elif "ANO" in df.columns: index_padrao = list(df.columns).index("ANO")
    elif "CATEGORIA" in df.columns: index_padrao = list(df.columns).index("CATEGORIA")

    eixo_x_view = st.selectbox("Eixo X (Agrupamento):", list(df.columns), index=index_padrao, key="sel_x")
    
    idx_y = list(numericas).index(col_kpi_padrao) if col_kpi_padrao in numericas else 0
    eixo_y_view = st.selectbox("Eixo Y (Valor):", numericas, index=idx_y, key="sel_y")

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
    if st.button("✨ Analisar com IA", type="primary", key="btn_ia"):
        with st.spinner("Analisando padrões..."):
            analise = analisar_com_ia(df, eixo_x_view, eixo_y_view)
            st.session_state["analise_ia"] = analise

if "analise_ia" in st.session_state:
    st.info(st.session_state["analise_ia"])

# ============================================================
# EXPORTAÇÃO
# ============================================================

st.markdown("---")
st.subheader("📄 Relatório PDF")

col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

if "pdf_bytes" not in st.session_state:
    st.session_state["pdf_bytes"] = None

with col_btn2:
    if st.button("📄 Gerar Relatório PDF", type="primary", key="btn_pdf"):
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
                st.success("Relatório pronto! Baixe abaixo.")
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")

    if st.session_state["pdf_bytes"] is not None:
        st.download_button(
            "⬇️ Baixar PDF",
            st.session_state["pdf_bytes"],
            "Relatorio_Platero_Pro.pdf",
            "application/pdf",
            type="primary",
            key="dl_pdf"
        )
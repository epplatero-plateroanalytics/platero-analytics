import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st

DB_FILE = "historico_platero.db"

# ============================================================
# FUNÇÃO AUXILIAR — CONEXÃO SEGURA
# ============================================================

def get_connection():
    """Retorna conexão segura com SQLite, compatível com Streamlit."""
    return sqlite3.connect(DB_FILE, check_same_thread=False)

# ============================================================
# INICIALIZAÇÃO DO BANCO
# ============================================================

def init_db():
    """Cria a tabela de histórico se ela não existir."""
    try:
        with get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS historico (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    usuario TEXT,
                    data_upload TEXT,
                    nome_arquivo TEXT,
                    faturamento_total REAL,
                    ticket_medio REAL,
                    linhas_processadas INTEGER
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_usuario ON historico(usuario)")
            conn.commit()
    except Exception as e:
        st.error(f"Erro ao inicializar banco: {e}")

# ============================================================
# SALVAR REGISTRO
# ============================================================

def salvar_registro(usuario, nome_arquivo, df, col_valor):
    """Salva o resumo da planilha no banco de dados."""
    try:
        if col_valor not in df.columns:
            st.error(f"Coluna '{col_valor}' não encontrada no DataFrame.")
            return False

        serie = pd.to_numeric(df[col_valor], errors="coerce")
        total = float(serie.sum(skipna=True))
        media = float(serie.mean(skipna=True))
        linhas = int(len(df))
        data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")

        with get_connection() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO historico 
                (usuario, data_upload, nome_arquivo, faturamento_total, ticket_medio, linhas_processadas)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (usuario, data_hoje, nome_arquivo, total, media, linhas))
            conn.commit()

        return True

    except Exception as e:
        st.error(f"Erro ao salvar no banco: {e}")
        return False

# ============================================================
# CARREGAR HISTÓRICO
# ============================================================

def carregar_historico(usuario):
    """Lê todo o histórico de um usuário específico."""
    try:
        with get_connection() as conn:
            query = """
                SELECT 
                    data_upload,
                    nome_arquivo,
                    faturamento_total,
                    ticket_medio
                FROM historico
                WHERE usuario = ?
                ORDER BY id DESC
            """
            df = pd.read_sql_query(query, conn, params=(usuario,))
        return df

    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")
        return pd.DataFrame()
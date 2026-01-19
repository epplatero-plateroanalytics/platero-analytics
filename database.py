import sqlite3
import pandas as pd
from datetime import datetime
import streamlit as st

# Nome do arquivo do banco de dados
DB_FILE = "historico_platero.db"

def init_db():
    """Cria a tabela de histórico se ela não existir."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            data_upload TEXT,
            nome_arquivo TEXT,
            faturamento_total REAL,
            ticket_medio REAL,
            linhas_processadas INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def salvar_registro(usuario, nome_arquivo, df, col_valor):
    """Salva o resumo da planilha no banco de dados."""
    try:
        # Calcula os KPIs para salvar
        total = df[col_valor].sum()
        media = df[col_valor].mean()
        linhas = len(df)
        data_hoje = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
            INSERT INTO historico (usuario, data_upload, nome_arquivo, faturamento_total, ticket_medio, linhas_processadas)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (usuario, data_hoje, nome_arquivo, total, media, linhas))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao salvar no banco: {e}")
        return False

def carregar_historico(usuario):
    """Lê todo o histórico de um usuário específico."""
    conn = sqlite3.connect(DB_FILE)
    query = f"SELECT data_upload, nome_arquivo, faturamento_total, ticket_medio FROM historico WHERE usuario = '{usuario}' ORDER BY id DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
import pandas as pd
import numpy as np
import streamlit as st

def limpar_planilha(df):
    """
    Faz a limpeza pesada dos dados:
    1. Remove colunas 'Unnamed' (lixo do Excel).
    2. Remove linhas de 'Total' ou vazias.
    3. Converte colunas de dinheiro (R$) para números puros.
    """
    
    # 1. REMOVER COLUNAS FANTASMAS (Unnamed)
    # Mantém apenas colunas que NÃO começam com "Unnamed"
    cols_validas = [c for c in df.columns if not str(c).startswith("Unnamed")]
    df = df[cols_validas]

    # 2. REMOVER LINHAS VAZIAS
    df = df.dropna(how='all')

    # 3. CONVERTER DATA (Se existir coluna 'Data')
    cols_data = [c for c in df.columns if 'DATA' in str(c).upper()]
    for col in cols_data:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    # 4. LIMPEZA DE NÚMEROS E DINHEIRO
    for col in df.columns:
        if df[col].dtype == 'object':
            series_limpa = df[col].astype(str).str.replace('R$', '', regex=False)
            series_limpa = series_limpa.str.replace('.', '', regex=False) # Tira ponto milhar
            series_limpa = series_limpa.str.replace(',', '.', regex=False) # Troca vírgula
            try:
                df[col] = pd.to_numeric(series_limpa)
            except:
                pass 

    # 5. REMOVER A LINHA DE "TOTAL" (O SEGREDO!)
    # Procura a palavra "Total" ou "TOTAL" em qualquer coluna e exclui a linha
    for col in df.select_dtypes(include=['object']).columns:
        df = df[~df[col].astype(str).str.contains("TOTAL", case=False, na=False)]
        df = df[~df[col].astype(str).str.contains("Total", case=False, na=False)]

    return df
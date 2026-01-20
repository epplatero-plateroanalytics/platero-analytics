import pandas as pd
import numpy as np
import streamlit as st

def limpar_planilha(df):
    """
    Limpeza Blindada V3:
    1. Protege contra nomes de colunas numéricos (Erro Attribute).
    2. Remove colunas vazias/fantasmas.
    3. Converte Dinheiro para Número (FORÇADO).
    4. Remove linhas de Total.
    """
    
    # 1. REMOVER COLUNAS "Unnamed" (Lixo do Excel)
    # Convertemos str(c) para evitar erro se a coluna for número
    cols_validas = [c for c in df.columns if not str(c).startswith("Unnamed")]
    df = df[cols_validas]

    # 2. CONVERTER DADOS
    for col in df.columns:
        # Garante que o nome da coluna seja texto para a verificação
        nome_coluna = str(col).upper()

        # Se a coluna for texto (Object), tenta limpar
        if df[col].dtype == 'object':
            
            # Limpeza visual: Tira R$, espaços e pontos de milhar
            # Converte a coluna para string antes de limpar para evitar erros
            col_limpa = df[col].astype(str).str.replace('R$', '', regex=False)
            col_limpa = col_limpa.str.replace(' ', '', regex=False)
            col_limpa = col_limpa.str.replace('.', '', regex=False) 
            col_limpa = col_limpa.str.replace(',', '.', regex=False)
            
            # Tenta converter para DATA (usando o nome seguro)
            if 'DATA' in nome_coluna or 'DATE' in nome_coluna:
                df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Tenta converter para NÚMERO (Com força bruta)
            else:
                try:
                    # Verifica se parece número (contém dígitos)
                    if col_limpa.str.match(r'^-?\d+(?:\.\d+)?$').any():
                        df[col] = pd.to_numeric(col_limpa, errors='coerce')
                except:
                    pass 

    # 3. REMOVER LINHAS DE "TOTAL"
    for col in df.select_dtypes(include=['object']).columns:
        # Converte para string antes de buscar 'Total'
        df = df[~df[col].astype(str).str.contains("TOTAL", case=False, na=False)]
        df = df[~df[col].astype(str).str.contains("Total", case=False, na=False)]

    # 4. REMOVER LINHAS VAZIAS
    df = df.dropna(how='all')

    return df
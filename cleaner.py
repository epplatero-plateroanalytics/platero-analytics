import pandas as pd
import numpy as np
import streamlit as st

def limpar_planilha(df):
    """
    Limpeza Agressiva V2:
    1. Remove colunas vazias/fantasmas.
    2. Converte Dinheiro para Número (FORÇADO).
    3. Remove linhas de Total.
    """
    
    # 1. REMOVER COLUNAS "Unnamed" (Lixo do Excel)
    cols_validas = [c for c in df.columns if not str(c).startswith("Unnamed")]
    df = df[cols_validas]

    # 2. CONVERTER DADOS (O Segredo está aqui!)
    for col in df.columns:
        # Se a coluna for texto (Object), tenta limpar
        if df[col].dtype == 'object':
            
            # Limpeza visual: Tira R$, espaços e pontos de milhar
            col_limpa = df[col].astype(str).str.replace('R$', '', regex=False)
            col_limpa = col_limpa.str.replace(' ', '', regex=False)
            col_limpa = col_limpa.str.replace('.', '', regex=False) # Tira ponto de milhar (1.000 -> 1000)
            col_limpa = col_limpa.str.replace(',', '.', regex=False) # Troca vírgula decimal (10,50 -> 10.50)
            
            # Tenta converter para DATA
            if 'DATA' in col.upper():
                df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Tenta converter para NÚMERO (Com força bruta: errors='coerce')
            else:
                # O 'coerce' transforma textos estranhos em NaNs (Vazio) em vez de travar
                try:
                    # Verifica se parece número antes de forçar
                    pd.to_numeric(col_limpa) 
                    df[col] = pd.to_numeric(col_limpa, errors='coerce')
                except:
                    pass # Se não for número mesmo (ex: Nome do Cliente), deixa quieto

    # 3. REMOVER LINHAS DE "TOTAL" (Que estragam a média)
    for col in df.select_dtypes(include=['object']).columns:
        # Remove linhas que tenham "Total" ou "TOTAL"
        df = df[~df[col].astype(str).str.contains("TOTAL", case=False, na=False)]
        df = df[~df[col].astype(str).str.contains("Total", case=False, na=False)]

    # 4. REMOVER LINHAS VAZIAS (Que sobraram da conversão)
    df = df.dropna(how='all')

    return df
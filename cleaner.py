import pandas as pd

def limpar_planilha(df):
    # Remove linhas totalmente vazias
    df = df.dropna(how='all')
    
    # Remove colunas totalmente vazias
    df = df.dropna(axis=1, how='all')
    
    # Tenta converter cabeçalhos para string para evitar erro
    df.columns = df.columns.astype(str)
    
    return df
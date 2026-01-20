import pandas as pd
import numpy as np
import streamlit as st

def encontrar_linha_cabecalho(df_temp):
    """
    Estratégia Infalível:
    Varre as primeiras 20 linhas e escolhe aquela que tem
    o MAIOR número de colunas preenchidas (não nulas).
    Isso evita pegar o título (que geralmente é só 1 célula preenchida).
    """
    max_cols_preenchidas = 0
    melhor_linha = 0
    
    # Limite de busca (primeiras 20 linhas)
    limite = min(20, len(df_temp))
    
    for i in range(limite):
        linha = df_temp.iloc[i]
        # Conta quantas células nessa linha NÃO são vazias/NaN
        cols_preenchidas = linha.count()
        
        # Se essa linha tem mais colunas preenchidas que a campeã anterior, ela assume a liderança
        # Dica: Headers reais costumam ter mais de 3 colunas preenchidas
        if cols_preenchidas > max_cols_preenchidas:
            max_cols_preenchidas = cols_preenchidas
            melhor_linha = i
            
    # Se achou uma linha com pouca coisa (ex: só 1 coluna), força buscar palavras-chave
    if max_cols_preenchidas <= 1:
        for i in range(limite):
            texto_linha = df_temp.iloc[i].astype(str).str.upper().sum()
            if 'DATA' in texto_linha or 'CLIENTE' in texto_linha or 'VALOR' in texto_linha:
                return i

    return melhor_linha

def carregar_e_limpar_inteligente(arquivo):
    lista_dfs = []
    
    # 1. LEITURA BRUTA (Sem cabeçalho definido)
    try:
        if arquivo.name.endswith('.xlsx'):
            dfs_dict = pd.read_excel(arquivo, sheet_name=None, header=None)
        else:
            dfs_dict = {'CSV': pd.read_csv(arquivo, header=None, sep=None, engine='python')}
    except Exception as e:
        return None, f"Erro crítico na leitura: {e}"

    # 2. PROCESSAMENTO POR ABA
    for nome_aba, df_raw in dfs_dict.items():
        if df_raw.empty: continue
        
        # A. Acha a linha certa (A que tem mais dados)
        idx_header = encontrar_linha_cabecalho(df_raw)
        
        # B. Redefine o DataFrame
        df_aba = df_raw.iloc[idx_header+1:].copy()
        df_aba.columns = df_raw.iloc[idx_header] # Usa a linha campeã como título
        
        # C. Remove colunas sem nome (NaN ou Unnamed)
        cols_validas = []
        for c in df_aba.columns:
            c_str = str(c).strip().upper()
            if c_str != 'NAN' and c_str != 'NONE' and not str(c).startswith('Unnamed'):
                cols_validas.append(c)
        
        if not cols_validas: continue # Se não sobrou coluna, pula essa aba
        
        df_aba = df_aba[cols_validas]
        df_aba['Origem_Aba'] = nome_aba
        lista_dfs.append(df_aba)

    if not lista_dfs:
        return None, "Não conseguimos identificar colunas válidas. Verifique se a planilha não está vazia."

    # 3. CONSOLIDAÇÃO
    df_final = pd.concat(lista_dfs, ignore_index=True)
    
    # 4. LIMPEZA DE DADOS (Dinheiro e Data)
    # Remove linhas de Total perdidas no meio
    for col in df_final.columns:
        if df_final[col].dtype == 'object':
            df_final = df_final[~df_final[col].astype(str).str.contains("TOTAL", case=False, na=False)]

    # Converte Valores
    for col in df_final.columns:
        col_str = str(col).upper()
        # Se for Valor/R$/Comissão
        if any(x in col_str for x in ['VALOR', 'R$', 'COMISSÃO', 'PREÇO', 'AMOUNT']):
            if df_final[col].dtype == 'object':
                df_final[col] = df_final[col].astype(str).str.replace('R$', '', regex=False)
                df_final[col] = df_final[col].astype(str).str.replace('.', '', regex=False)
                df_final[col] = df_final[col].astype(str).str.replace(',', '.', regex=False)
                df_final[col] = pd.to_numeric(df_final[col], errors='coerce')
        
        # Se for Data
        if 'DATA' in col_str:
            df_final[col] = pd.to_datetime(df_final[col], errors='coerce')

    df_final = df_final.dropna(how='all')
    
    return df_final, None
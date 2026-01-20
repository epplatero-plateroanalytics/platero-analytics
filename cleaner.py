import pandas as pd
import numpy as np
import streamlit as st
import re

def encontrar_linha_cabecalho(df_temp):
    """
    Estratégia: Busca a linha com mais colunas preenchidas.
    """
    max_cols = 0
    melhor_linha = 0
    limite = min(20, len(df_temp))
    
    for i in range(limite):
        linha = df_temp.iloc[i]
        cols_preenchidas = linha.count()
        if cols_preenchidas > max_cols:
            max_cols = cols_preenchidas
            melhor_linha = i
            
    if max_cols <= 1:
        for i in range(limite):
            txt = df_temp.iloc[i].astype(str).str.upper().sum()
            if any(x in txt for x in ['DATA', 'VALOR', 'VENDAS', 'ANO', 'CLIENTE']):
                return i
    return melhor_linha

def carregar_e_limpar_inteligente(arquivo):
    lista_dfs = []
    
    # 1. LEITURA BRUTA
    try:
        if arquivo.name.endswith('.xlsx'):
            dfs_dict = pd.read_excel(arquivo, sheet_name=None, header=None)
        else:
            dfs_dict = {'CSV': pd.read_csv(arquivo, header=None, sep=None, engine='python')}
    except Exception as e:
        return None, f"Erro na leitura: {e}"

    # 2. PROCESSAMENTO POR ABA
    for nome_aba, df_raw in dfs_dict.items():
        if df_raw.empty: continue
        
        # Acha cabeçalho
        idx_header = encontrar_linha_cabecalho(df_raw)
        
        # Recorta
        df_aba = df_raw.iloc[idx_header+1:].copy()
        df_aba.columns = df_raw.iloc[idx_header]
        
        # Remove colunas vazias
        cols_validas = []
        for c in df_aba.columns:
            c_str = str(c).strip().upper()
            if c_str != 'NAN' and not str(c).startswith('Unnamed'):
                cols_validas.append(c)
        
        if not cols_validas: continue
        
        df_aba = df_aba[cols_validas]
        df_aba['Origem_Aba'] = nome_aba
        lista_dfs.append(df_aba)

    if not lista_dfs:
        return None, "Nenhuma tabela válida encontrada."

    # 3. CONSOLIDAÇÃO
    df_final = pd.concat(lista_dfs, ignore_index=True)

    # 4. LIMPEZA "RAIO-X" (Verifica o conteúdo, não só o nome)
    
    # A. Remove linhas de Total
    for col in df_final.columns:
        if df_final[col].dtype == 'object':
            df_final = df_final[~df_final[col].astype(str).str.contains("TOTAL", case=False, na=False)]

    # B. Loop Universal de Conversão
    for col in df_final.columns:
        # Se já for número, pula
        if pd.api.types.is_numeric_dtype(df_final[col]):
            continue
            
        col_str_upper = str(col).upper()
        
        # Se for DATA pelo nome
        if any(x in col_str_upper for x in ['DATA', 'DATE', 'VENCIMENTO']):
            df_final[col] = pd.to_datetime(df_final[col], errors='coerce')
            continue

        # TENTATIVA DE CONVERSÃO NUMÉRICA (O Pulo do Gato)
        # Pega a coluna como texto
        series_texto = df_final[col].astype(str)
        
        # Limpa sujeiras comuns (R$, espaços, símbolos)
        series_limpa = series_texto.str.replace('R$', '', regex=False).str.strip()
        
        # Tenta conversão formato US (1000.00)
        num_us = pd.to_numeric(series_limpa, errors='coerce')
        
        # Tenta conversão formato BR (1.000,00 -> 1000.00)
        series_br = series_limpa.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        num_br = pd.to_numeric(series_br, errors='coerce')
        
        # CONTAGEM DE SUCESSO
        # Conta quantos números válidos conseguimos resgatar
        validos_us = num_us.notna().sum()
        validos_br = num_br.notna().sum()
        total_linhas = len(df_final)
        
        # SE MAIS DE 40% DA COLUNA VIROU NÚMERO -> É UMA COLUNA NUMÉRICA!
        # Ou se o nome da coluna for muito óbvio (VENDAS, ANO, VALOR)
        eh_nome_numerico = any(x in col_str_upper for x in ['VALOR', 'VENDAS', 'ANO', 'COMISSÃO', 'PREÇO', 'QTD'])
        
        if validos_us > total_linhas * 0.4 or (eh_nome_numerico and validos_us > 0):
            df_final[col] = num_us # Aplica a conversão
        elif validos_br > total_linhas * 0.4 or (eh_nome_numerico and validos_br > 0):
            df_final[col] = num_br # Aplica a conversão

    # 5. REMOVE LINHAS VAZIAS (Pós-conversão)
    df_final = df_final.dropna(how='all')
    
    return df_final, None
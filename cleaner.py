import pandas as pd
import numpy as np
import streamlit as st
import re

def encontrar_linha_cabecalho(df_temp):
    """
    Varre as primeiras linhas para achar onde está o cabeçalho real.
    Critério: A linha que tiver palavras-chave de negócio (Data, Valor, Cliente).
    """
    palavras_chave = ['DATA', 'DATE', 'VALOR', 'VLR', 'R$', 'TOTAL', 'CLIENTE', 'NOME', 'DESCRIÇÃO', 'HISTÓRICO']
    
    # Varre as primeiras 10 linhas
    for i in range(min(15, len(df_temp))):
        linha = df_temp.iloc[i].astype(str).str.upper().tolist()
        # Conta quantas palavras chave aparecem nesta linha
        matches = sum(1 for celula in linha for key in palavras_chave if key in celula)
        
        # Se encontrar pelo menos 2 palavras-chave, assumimos que é o cabeçalho
        if matches >= 2:
            return i
    return 0 # Se não achar nada, assume a primeira

def normalizar_colunas(cols):
    """Padroniza nomes de colunas para facilitar a IA e os Gráficos."""
    novas_cols = []
    for col in cols:
        c = str(col).strip().upper()
        if 'DATA' in c or 'DATE' in c: novas_cols.append('DATA')
        elif 'VALOR' in c or 'VLR' in c or 'TOTAL' in c or 'AMOUNT' in c: novas_cols.append('VALOR')
        elif 'CLIENTE' in c or 'NOME' in c: novas_cols.append('CLIENTE')
        elif 'PRODUTO' in c: novas_cols.append('PRODUTO')
        else: novas_cols.append(c)
    return novas_cols

def carregar_e_limpar_inteligente(arquivo):
    """
    Função Mestra: Lê Excel (todas abas) ou CSV, acha cabeçalho,
    limpa sujeira e retorna um DF pronto para análise.
    """
    lista_dfs = []
    
    # 1. LEITURA BRUTA (Lê tudo como texto primeiro para não perder nada)
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
        
        # A. Descobre onde começa o dado real
        idx_header = encontrar_linha_cabecalho(df_raw)
        
        # B. Redefine o DataFrame a partir daquela linha
        df_aba = df_raw.iloc[idx_header+1:].copy()
        df_aba.columns = df_raw.iloc[idx_header] # Usa a linha descoberta como título
        
        # C. Remove colunas vazias/sem nome
        cols_validas = [c for c in df_aba.columns if str(c).upper() != 'NAN' and not str(c).startswith('Unnamed')]
        df_aba = df_aba[cols_validas]
        
        # D. Adiciona Origem (Ano/Aba)
        df_aba['Origem_Aba'] = nome_aba
        lista_dfs.append(df_aba)

    if not lista_dfs:
        return None, "Nenhuma aba válida encontrada."

    # 3. CONSOLIDAÇÃO
    df_final = pd.concat(lista_dfs, ignore_index=True)
    
    # 4. LIMPEZA FINA (Tipos de Dados)
    # Padroniza nomes das colunas
    # df_final.columns = normalizar_colunas(df_final.columns) # Opcional: Ative se quiser forçar nomes padrão
    
    # Remove linhas de Totais perdidas
    col_texto = [c for c in df_final.columns if df_final[c].dtype == 'object']
    for col in col_texto:
        df_final = df_final[~df_final[col].astype(str).str.contains("TOTAL", case=False, na=False)]

    # Converte Dinheiro e Data
    for col in df_final.columns:
        col_str = str(col).upper()
        
        # Limpeza de Dinheiro
        if 'VALOR' in col_str or 'R$' in col_str or 'COMISSÃO' in col_str or 'PREÇO' in col_str:
            if df_final[col].dtype == 'object':
                df_final[col] = df_final[col].astype(str).str.replace('R$', '', regex=False)
                df_final[col] = df_final[col].astype(str).str.replace('.', '', regex=False)
                df_final[col] = df_final[col].astype(str).str.replace(',', '.', regex=False)
                df_final[col] = pd.to_numeric(df_final[col], errors='coerce')
        
        # Limpeza de Data
        if 'DATA' in col_str:
            df_final[col] = pd.to_datetime(df_final[col], errors='coerce')

    df_final = df_final.dropna(how='all') # Remove linhas vazias
    
    return df_final, None
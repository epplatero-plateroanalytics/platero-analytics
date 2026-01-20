import pandas as pd
import numpy as np
import streamlit as st

def encontrar_linha_cabecalho(df_temp):
    """
    Estratégia Infalível V2:
    Procura a linha com mais colunas preenchidas.
    """
    max_cols_preenchidas = 0
    melhor_linha = 0
    limite = min(20, len(df_temp))
    
    for i in range(limite):
        linha = df_temp.iloc[i]
        cols_preenchidas = linha.count()
        if cols_preenchidas > max_cols_preenchidas:
            max_cols_preenchidas = cols_preenchidas
            melhor_linha = i
            
    # Proteção: Se a melhor linha tiver só 1 coluna, tenta achar palavras-chave
    if max_cols_preenchidas <= 1:
        for i in range(limite):
            txt = df_temp.iloc[i].astype(str).str.upper().sum()
            if any(x in txt for x in ['DATA', 'VALOR', 'VENDAS', 'ANO', 'CLIENTE']):
                return i

    return melhor_linha

def carregar_e_limpar_inteligente(arquivo):
    lista_dfs = []
    
    # 1. LEITURA
    try:
        if arquivo.name.endswith('.xlsx'):
            dfs_dict = pd.read_excel(arquivo, sheet_name=None, header=None)
        else:
            dfs_dict = {'CSV': pd.read_csv(arquivo, header=None, sep=None, engine='python')}
    except Exception as e:
        return None, f"Erro na leitura: {e}"

    # 2. PROCESSAMENTO
    for nome_aba, df_raw in dfs_dict.items():
        if df_raw.empty: continue
        
        # Acha o cabeçalho
        idx_header = encontrar_linha_cabecalho(df_raw)
        
        # Recorta a tabela
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
        return None, "Planilha vazia ou ilegível."

    # 3. CONSOLIDAÇÃO
    df_final = pd.concat(lista_dfs, ignore_index=True)
    
    # 4. LIMPEZA UNIVERSAL (O Segredo!)
    # Remove linhas de Total
    for col in df_final.columns:
        if df_final[col].dtype == 'object':
            df_final = df_final[~df_final[col].astype(str).str.contains("TOTAL", case=False, na=False)]

    # Tenta converter TODAS as colunas
    for col in df_final.columns:
        col_str = str(col).upper()
        
        # Se for Data explicitamente
        if 'DATA' in col_str or 'DATE' in col_str:
            df_final[col] = pd.to_datetime(df_final[col], errors='coerce')
        
        # Para todas as outras, tenta virar número (Vendas, Ano, Meta, etc)
        else:
            # Estratégia Híbrida (US vs BR)
            # 1. Tenta direto (ex: 205252.93)
            s_direta = pd.to_numeric(df_final[col], errors='coerce')
            
            # 2. Tenta formato BR (ex: 205.252,93)
            if df_final[col].dtype == 'object':
                s_limpa_br = df_final[col].astype(str).str.replace('R$', '', regex=False)
                s_limpa_br = s_limpa_br.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                s_br = pd.to_numeric(s_limpa_br, errors='coerce')
            else:
                s_br = s_direta # Já era numérico

            # Vence quem converter mais dados
            validos_direta = s_direta.notna().sum()
            validos_br = s_br.notna().sum()

            # Se a conversão salvou mais de 50% dos dados, aplica!
            if validos_direta > len(df_final) * 0.5:
                df_final[col] = s_direta
            elif validos_br > len(df_final) * 0.5:
                df_final[col] = s_br
            # Se falhou (ex: Coluna "Nome do Cliente"), mantém como texto original

    df_final = df_final.dropna(how='all')
    
    return df_final, None
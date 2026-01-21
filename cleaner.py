import pandas as pd
import numpy as np
import streamlit as st
import re

def encontrar_linha_cabecalho(df_temp):
    limite = min(20, len(df_temp))
    max_cols = 0
    melhor_linha = 0

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

    # 1. LEITURA
    try:
        if arquivo.name.endswith('.xlsx'):
            dfs_dict = pd.read_excel(arquivo, sheet_name=None, header=None)
        else:
            dfs_dict = {'CSV': pd.read_csv(arquivo, header=None, sep=None, engine='python')}
    except Exception as e:
        return None, f"Erro na leitura: {e}"

    # 2. PROCESSAMENTO POR ABA
    for nome_aba, df_raw in dfs_dict.items():
        if df_raw.empty:
            continue

        idx_header = encontrar_linha_cabecalho(df_raw)

        df_aba = df_raw.iloc[idx_header+1:].copy()
        df_aba.columns = df_raw.iloc[idx_header]

        # Remove colunas vazias
        cols_validas = [
            c for c in df_aba.columns
            if str(c).strip().upper() != 'NAN' and not str(c).startswith('Unnamed')
        ]

        if not cols_validas:
            continue

        df_aba = df_aba[cols_validas]
        df_aba['Origem_Aba'] = nome_aba
        lista_dfs.append(df_aba)

    if not lista_dfs:
        return None, "Nenhuma tabela válida encontrada."

    # 3. CONSOLIDAÇÃO
    df_final = pd.concat(lista_dfs, ignore_index=True)

    # 4. LIMPEZA DE LINHAS DE TOTAL
    for col in df_final.columns:
        if df_final[col].dtype == 'object':
            df_final = df_final[~df_final[col].astype(str).str.contains("TOTAL", case=False, na=False)]

    # 5. DETECÇÃO DE DATAS
    for col in df_final.columns:
        if any(x in str(col).upper() for x in ['DATA', 'DATE', 'VENC']):
            df_final[col] = pd.to_datetime(df_final[col], errors='coerce')

    # 6. LIMPEZA E CONVERSÃO NUMÉRICA UNIVERSAL
    for col in df_final.columns:
        if pd.api.types.is_numeric_dtype(df_final[col]):
            continue

        serie = df_final[col].astype(str)

        # remove símbolos comuns
        serie = (
            serie.str.replace('R$', '', regex=False)
                 .str.replace(' ', '', regex=False)
                 .str.replace('\t', '', regex=False)
                 .str.replace('\n', '', regex=False)
        )

        # tenta BR → remove pontos e troca vírgula por ponto
        serie_br = serie.str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
        num_br = pd.to_numeric(serie_br, errors='coerce')

        # tenta US
        num_us = pd.to_numeric(serie, errors='coerce')

        # escolhe o que converteu mais
        if num_br.notna().sum() >= num_us.notna().sum():
            melhor = num_br
        else:
            melhor = num_us

        # aplica se houver pelo menos 1 número
        if melhor.notna().sum() > 0:
            df_final[col] = melhor

    # 7. REMOVE LINHAS TOTALMENTE VAZIAS
    df_final = df_final.dropna(how='all')

    return df_final, None
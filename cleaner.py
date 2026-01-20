import pandas as pd
import numpy as np
import streamlit as st

def encontrar_linha_cabecalho(df_temp):
    """
    Estratégia: Busca a linha com mais colunas preenchidas.
    """
    max_cols = 0
    melhor_linha = 0
    limite = min(20, len(df_temp))
    
    for i in range(limite):
        linha = df_temp.iloc[i]
        # Conta células não vazias
        cols_preenchidas = linha.count()
        if cols_preenchidas > max_cols:
            max_cols = cols_preenchidas
            melhor_linha = i
            
    # Se achou pouco, tenta palavras-chave
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
        
        # Remove colunas inúteis
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

    # === [AQUI ESTÁ A CORREÇÃO PRINCIPAL] ===
    # Remove linhas vazias AGORA, antes de converter
    df_final = df_final.dropna(how='all')
    
    # Remove linhas de Total perdidas
    for col in df_final.columns:
        if df_final[col].dtype == 'object':
            df_final = df_final[~df_final[col].astype(str).str.contains("TOTAL", case=False, na=False)]

    # 4. CONVERSÃO "DITADORA" (Obriga a virar número)
    for col in df_final.columns:
        col_str = str(col).upper()
        
        # Lista de nomes que TEM QUE SER NÚMERO
        palavras_numero = ['VALOR', 'R$', 'COMISSÃO', 'PREÇO', 'AMOUNT', 'VENDAS', 'SALDO', 'TOTAL', 'ANO', 'META', 'QTD']
        
        # Lista de nomes que TEM QUE SER DATA
        palavras_data = ['DATA', 'DATE', 'VENCIMENTO', 'EMISSÃO']

        # A. Se for DATA
        if any(p in col_str for p in palavras_data):
            df_final[col] = pd.to_datetime(df_final[col], errors='coerce')
        
        # B. Se for NÚMERO (Força Bruta)
        elif any(p in col_str for p in palavras_numero):
            # Limpa caracteres de moeda BR
            if df_final[col].dtype == 'object':
                s_limpa = df_final[col].astype(str).str.replace('R$', '', regex=False)
                s_limpa = s_limpa.str.replace('.', '', regex=False).str.replace(',', '.', regex=False) # 1.000,00 -> 1000.00
                
                # Tenta converter o limpo (BR)
                s_convertida = pd.to_numeric(s_limpa, errors='coerce')
                
                # Se falhar muito (ficou tudo vazio), tenta o original (formato US: 1000.00)
                if s_convertida.notna().sum() == 0:
                     df_final[col] = pd.to_numeric(df_final[col], errors='coerce')
                else:
                     df_final[col] = s_convertida
            else:
                # Se já não for objeto, garante que é numérico
                df_final[col] = pd.to_numeric(df_final[col], errors='coerce')

        # C. Se não tiver nome óbvio, tenta adivinhar (Regra dos 50%)
        else:
            s_num = pd.to_numeric(df_final[col], errors='coerce')
            if s_num.notna().sum() > len(df_final) * 0.5:
                df_final[col] = s_num

    df_final = df_final.dropna(how='all')
    
    return df_final, None
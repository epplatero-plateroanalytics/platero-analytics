import pandas as pd
import numpy as np
import re

def detectar_tipos(df):
    datas = []
    numericas = []
    categoricas = []
    monetarias = []
    quantidades = []
    booleanas = []
    texto_livre = []

    # Pré-processamento rápido
    df_str = df.astype(str)

    # Padrões
    padrao_data = r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
    padrao_moeda = r"(R\$|USD|EUR|REAL|PREÇO|VALOR|PRICE)"
    padrao_booleano = {"SIM", "NÃO", "NAO", "YES", "NO", "TRUE", "FALSE", "0", "1"}

    for col in df.columns:
        serie = df[col]
        serie_str = df_str[col].str.strip()

        # ============================================================
        # 1. DETECÇÃO DE DATAS (muito mais robusta)
        # ============================================================
        if pd.api.types.is_datetime64_any_dtype(serie):
            datas.append(col)
            continue

        amostra = serie_str.dropna().head(30)

        if amostra.str.contains(padrao_data, na=False, regex=True).mean() > 0.5:
            try:
                pd.to_datetime(serie, errors="raise", dayfirst=True)
                datas.append(col)
                continue
            except:
                pass

        # ============================================================
        # 2. DETECÇÃO DE BOOLEANOS (melhorada)
        # ============================================================
        valores_unicos = set(serie_str.dropna().str.upper().unique())

        if len(valores_unicos) <= 4 and valores_unicos.issubset(padrao_booleano):
            booleanas.append(col)
            continue

        # ============================================================
        # 3. DETECÇÃO DE NÚMEROS (muito mais precisa)
        # ============================================================
        if pd.api.types.is_numeric_dtype(serie):
            numericas.append(col)
            continue

        # Limpeza inteligente
        amostra_limpa = (
            amostra.str.replace("R$", "", regex=False)
                   .str.replace("%", "", regex=False)
                   .str.replace(".", "", regex=False)
                   .str.replace(",", ".", regex=False)
                   .str.replace(" ", "", regex=False)
        )

        conversao = pd.to_numeric(amostra_limpa, errors="coerce")

        if conversao.notna().mean() > 0.7:
            numericas.append(col)

            # Monetária
            if serie_str.str.contains(padrao_moeda, case=False, regex=True, na=False).mean() > 0.2:
                monetarias.append(col)

            # Quantidades
            if any(x in col.upper() for x in ["QTD", "QUANT", "VOLUME", "QTDE", "QUANTIDADE"]):
                quantidades.append(col)

            continue

        # ============================================================
        # 4. DETECÇÃO DE TEXTO LIVRE (melhorada)
        # ============================================================
        if serie_str.dropna().str.len().mean() > 50:
            texto_livre.append(col)
            continue

        # ============================================================
        # 5. DETECÇÃO DE CATEGÓRICAS (muito mais inteligente)
        # ============================================================
        unicos = serie.nunique(dropna=True)

        # Categóricas típicas
        if unicos <= 40:
            categoricas.append(col)
            continue

        # Strings curtas → categóricas
        if serie.dtype == object and serie_str.dropna().str.len().mean() < 20:
            categoricas.append(col)
            continue

        # Fallback
        categoricas.append(col)

    return {
        "datas": datas,
        "numericas": numericas,
        "categoricas": categoricas,
        "monetarias": monetarias,
        "quantidades": quantidades,
        "booleanas": booleanas,
        "texto_livre": texto_livre
    }
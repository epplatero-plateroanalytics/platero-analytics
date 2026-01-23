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

    for col in df.columns:
        serie = df[col]
        serie_str = serie.astype(str)

        # ============================================================
        # 1. DETECÇÃO DE DATAS (mesmo se vier como texto)
        # ============================================================
        if pd.api.types.is_datetime64_any_dtype(serie):
            datas.append(col)
            continue

        padrao_data = r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
        amostra = serie_str.dropna().head(20)

        if amostra.str.contains(padrao_data).mean() > 0.5:
            try:
                pd.to_datetime(serie, errors="raise")
                datas.append(col)
                continue
            except:
                pass

        # ============================================================
        # 2. DETECÇÃO DE BOOLEANOS
        # ============================================================
        valores_bool = {"SIM", "NAO", "NÃO", "YES", "NO", "TRUE", "FALSE", "0", "1"}
        if serie_str.dropna().str.upper().isin(valores_bool).mean() > 0.9:
            booleanas.append(col)
            continue

        # ============================================================
        # 3. DETECÇÃO DE NÚMEROS (mesmo se vier como texto)
        # ============================================================
        if pd.api.types.is_numeric_dtype(serie):
            numericas.append(col)
            continue

        amostra_limpa = (
            amostra.str.replace("R$", "", regex=False)
                   .str.replace("%", "", regex=False)
                   .str.replace(".", "", regex=False)
                   .str.replace(",", ".", regex=False)
                   .str.replace(" ", "", regex=False)
        )

        conversao = pd.to_numeric(amostra_limpa, errors="coerce")

        if conversao.notna().mean() > 0.6:
            numericas.append(col)

            # Detecta se é monetária
            if serie_str.str.contains("R\\$|USD|EUR|REAL|VALOR|PREÇO|PRICE", case=False, regex=True).mean() > 0.3:
                monetarias.append(col)

            # Detecta se é quantidade
            if any(x in col.upper() for x in ["QTD", "QUANT", "VOLUME", "QTDE", "QUANTIDADE"]):
                quantidades.append(col)

            continue

        # ============================================================
        # 4. DETECÇÃO DE TEXTO LIVRE
        # ============================================================
        # Textos longos → texto livre
        if serie_str.dropna().str.len().mean() > 40:
            texto_livre.append(col)
            continue

        # ============================================================
        # 5. DETECÇÃO DE CATEGÓRICAS
        # ============================================================
        # Poucos valores únicos → categórica
        if serie.nunique(dropna=True) <= 30:
            categoricas.append(col)
            continue

        # Strings → categóricas
        if serie.dtype == object:
            categoricas.append(col)
            continue

        # fallback
        categoricas.append(col)

    # ============================================================
    # RETORNO COMPLETO
    # ============================================================
    return {
        "datas": datas,
        "numericas": numericas,
        "categoricas": categoricas,
        "monetarias": monetarias,
        "quantidades": quantidades,
        "booleanas": booleanas,
        "texto_livre": texto_livre
    }
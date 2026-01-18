import pandas as pd

def detectar_tipos(df):
    numericas = []
    categoricas = []
    datas = []
    
    for col in df.columns:
        # Tenta identificar se é data
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            datas.append(col)
        # Tenta identificar se é número
        elif pd.api.types.is_numeric_dtype(df[col]):
            numericas.append(col)
        else:
            # Se não for nem um nem outro, assumimos texto/categoria
            categoricas.append(col)
            
    return datas, numericas, categoricas
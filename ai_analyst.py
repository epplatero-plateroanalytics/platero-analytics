import pandas as pd
import numpy as np

def analisar_com_ia(df, eixo_x, eixo_y):
    # ============================================================
    # PREPARAÇÃO E SEGURANÇA
    # ============================================================
    serie = pd.to_numeric(df[eixo_y], errors="coerce")
    total = float(serie.sum(skipna=True))
    media = float(serie.mean(skipna=True))
    qtd = len(df)
    desvio = float(serie.std(skipna=True))
    cv = (desvio / media * 100) if media != 0 else 0
    minimo = float(serie.min(skipna=True))
    maximo = float(serie.max(skipna=True))

    df_temp = df.copy()
    df_temp[eixo_x] = df_temp[eixo_x].astype(str)

    # ============================================================
    # 1. AGRUPAMENTO E CONCENTRAÇÃO
    # ============================================================
    agrupado = (
        df_temp.groupby(eixo_x)[eixo_y]
        .sum(min_count=1)
        .sort_values(ascending=False)
    )

    if len(agrupado) == 0:
        return "Não foi possível gerar análise: agrupamento vazio."

    maior_cat = agrupado.index[0]
    maior_val = agrupado.iloc[0]
    perc_maior = (maior_val / total * 100) if total > 0 else 0

    # ============================================================
    # 2. PARETO 80/20
    # ============================================================
    acumulado = agrupado.cumsum() / total if total > 0 else agrupado * 0
    categorias_pareto = acumulado[acumulado <= 0.80].index.tolist()
    qtd_pareto = len(categorias_pareto)
    perc_pareto = (qtd_pareto / len(agrupado) * 100) if len(agrupado) > 0 else 0

    # ============================================================
    # 3. OUTLIERS (IQR + Z-SCORE)
    # ============================================================
    q1 = serie.quantile(0.25)
    q3 = serie.quantile(0.75)
    iqr = q3 - q1
    limite_sup = q3 + 1.5 * iqr

    outliers_iqr = df_temp[serie > limite_sup]
    qtd_outliers_iqr = len(outliers_iqr)

    z_scores = (serie - media) / desvio if desvio > 0 else pd.Series([0] * len(serie))
    outliers_z = df_temp[z_scores > 3]
    qtd_outliers_z = len(outliers_z)

    # ============================================================
    # 4. DISTRIBUIÇÃO (ASSIMETRIA E CURTOSE)
    # ============================================================
    assimetria = float(serie.skew(skipna=True))
    curtose = float(serie.kurtosis(skipna=True))

    # ============================================================
    # 5. CORRELAÇÃO AUTOMÁTICA
    # ============================================================
    correlacoes = None
    try:
        df_num = df.select_dtypes(include=[np.number])
        if eixo_y in df_num.columns and len(df_num.columns) > 1:
            corr = df_num.corr()[eixo_y].drop(eixo_y).sort_values(ascending=False)
            correlacoes = corr.head(3)
    except:
        pass

    # ============================================================
    # 6. TENDÊNCIA TEMPORAL E SAZONALIDADE
    # ============================================================
    tendencia_texto = ""
    sazonalidade_texto = ""
    datas_validas = None

    for col in df.columns:
        if any(x in col.upper() for x in ["DATA", "DATE", "VENC", "EMISS"]):
            datas_validas = col
            break

    if datas_validas:
        df_tempo = df.copy()
        df_tempo[datas_validas] = pd.to_datetime(df_tempo[datas_validas], errors="coerce")
        df_tempo = df_tempo.dropna(subset=[datas_validas])

        if len(df_tempo) > 3:
            df_tempo["mes"] = df_tempo[datas_validas].dt.to_period("M")
            evolucao = df_tempo.groupby("mes")[eixo_y].sum()

            if len(evolucao) > 1:
                crescimento = evolucao.pct_change().mean() * 100
                if crescimento > 0:
                    tendencia_texto = f"A série temporal indica um crescimento médio de {crescimento:.1f}% ao mês."
                elif crescimento < 0:
                    tendencia_texto = f"Os dados mostram uma queda média de {abs(crescimento):.1f}% ao mês."
                else:
                    tendencia_texto = "A série temporal não apresenta tendência significativa."

            # Sazonalidade
            df_tempo["mes_num"] = df_tempo[datas_validas].dt.month
            sazonal = df_tempo.groupby("mes_num")[eixo_y].mean()

            if len(sazonal) > 0:
                mes_top = sazonal.idxmax()
                sazonalidade_texto = (
                    f"O mês com maior média histórica é **{mes_top}**, indicando possível sazonalidade."
                )

    # ============================================================
    # 7. QUALIDADE DOS DADOS
    # ============================================================
    nulos = df[eixo_y].isna().sum()
    perc_nulos = (nulos / qtd * 100) if qtd > 0 else 0

    # ============================================================
    # TEXTO FINAL — ULTRA PREMIUM
    # ============================================================
    texto = f"""
📌 **Resumo Executivo Avançado**

• Total acumulado de **{eixo_y}**: {total:,.2f}  
• Média por registro: {media:,.2f}  
• Desvio padrão: {desvio:,.2f}  
• Coeficiente de variação (CV): {cv:.1f}%  
• Intervalo observado: {minimo:,.2f} → {maximo:,.2f}  
• Registros analisados: {qtd}  

📌 **Concentração e Liderança**
• A categoria **{maior_cat}** lidera com {maior_val:,.2f}, representando **{perc_maior:.1f}%** do total.  
• Isso indica forte concentração em poucos grupos.

📌 **Pareto 80/20**
• **{qtd_pareto} categorias** ({perc_pareto:.1f}%) respondem por **80%** do resultado.  
• Focar nesses grupos tende a gerar maior impacto estratégico.

📌 **Outliers e Anomalias**
• Outliers pelo método IQR: **{qtd_outliers_iqr}**  
• Outliers pelo método Z‑Score (>3σ): **{qtd_outliers_z}**  
• Esses pontos podem indicar oportunidades, erros ou eventos excepcionais.

📌 **Distribuição Estatística**
• Assimetria: {assimetria:.2f}  
• Curtose: {curtose:.2f}  
"""

    if correlacoes is not None and len(correlacoes) > 0:
        texto += "📌 **Correlação com outras variáveis**\n"
        for col, val in correlacoes.items():
            texto += f"• Correlação com **{col}**: {val:.2f}\n"
        texto += "\n"

    if tendencia_texto:
        texto += f"📌 **Tendência Temporal**\n• {tendencia_texto}\n\n"

    if sazonalidade_texto:
        texto += f"📌 **Sazonalidade**\n• {sazonalidade_texto}\n\n"

    texto += f"""
📌 **Qualidade dos Dados**
• Valores nulos em {eixo_y}: {nulos} ({perc_nulos:.1f}%)  
• Recomenda-se revisar registros incompletos para evitar distorções.

📌 **Conclusão Estratégica**
A análise revela padrões claros de concentração, variabilidade e anomalias.  
Esses elementos podem orientar decisões como:

• Priorização de segmentos de maior impacto  
• Revisão de processos e detecção de erros  
• Identificação de riscos e oportunidades  
• Planejamento baseado em sazonalidade  
• Estratégias de crescimento sustentado  

Este diagnóstico fornece uma visão completa, combinando estatística avançada, análise temporal e inteligência executiva.
"""

    return texto
def analisar_com_ia(df, eixo_x, eixo_y):
    total = df[eixo_y].sum()
    media = df[eixo_y].mean()
    qtd = len(df)

    texto = f"""
Análise automática baseada nos dados fornecidos:

• Total acumulado de {eixo_y}: {total:.2f}
• Média por registro: {media:.2f}
• Registros analisados: {qtd}

Com base na coluna de agrupamento "{eixo_x}", é possível identificar padrões,
tendências e concentrações relevantes que podem orientar decisões estratégicas.
"""

    return texto
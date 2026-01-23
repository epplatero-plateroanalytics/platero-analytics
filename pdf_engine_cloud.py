import os
import tempfile
from datetime import datetime

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from fpdf import FPDF

# ============================================================
# CONFIGURAÇÕES GERAIS
# ============================================================

COR_AZUL = (0, 51, 102)
COR_CINZA = (85, 85, 85)
COR_CINZA_CLARO = (220, 220, 220)
COR_TEXTO = (40, 40, 40)
FONTE_PADRAO = "DejaVu"

PALETAS = [
    "viridis", "plasma", "inferno", "magma", "cividis",
    "coolwarm", "Spectral", "Set2", "Accent", "tab20"
]

def escolher_paleta(i):
    return PALETAS[i % len(PALETAS)]

# ============================================================
# CLASSE PDF
# ============================================================

class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # FONTES NA RAIZ DO PROJETO
        self.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
        self.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
        self.add_font("DejaVu", "I", "DejaVuSans-Oblique.ttf", uni=True)

        self.set_auto_page_break(auto=True, margin=15)
        self.alias_nb_pages()

    def header(self):
        self.set_text_color(240, 240, 240)
        self.set_font(FONTE_PADRAO, 'B', 42)
        self.set_xy(0, 110)
        self.cell(0, 10, 'PLATERO ANALYTICS', align='C')

        if os.path.exists('assets/logo.png'):
            self.image('assets/logo.png', 10, 8, w=28)

        self.set_y(12)
        self.set_text_color(*COR_AZUL)
        self.set_font(FONTE_PADRAO, 'B', 16)
        self.cell(0, 8, 'Relatório Executivo Completo', 0, 1, 'R')

        self.set_font(FONTE_PADRAO, '', 9)
        self.set_text_color(*COR_CINZA)
        data_str = datetime.now().strftime('%d/%m/%Y %H:%M')
        self.cell(0, 6, f'Gerado em {data_str}', 0, 1, 'R')

        self.set_draw_color(*COR_CINZA_CLARO)
        self.set_line_width(0.4)
        self.line(10, 28, 200, 28)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font(FONTE_PADRAO, '', 8)
        self.set_text_color(*COR_CINZA)
        self.cell(0, 10, f'Platero Analytics  |  Página {self.page_no()}/{{nb}}', 0, 0, 'C')

    def titulo_secao(self, texto, nivel=1):
        if nivel == 1:
            self.set_font(FONTE_PADRAO, 'B', 14)
            self.set_text_color(*COR_AZUL)
            self.ln(4)
            self.cell(0, 8, texto, ln=True)
            self.set_draw_color(*COR_AZUL)
            self.set_line_width(0.6)
            y = self.get_y()
            self.line(10, y, 200, y)
            self.ln(4)

        elif nivel == 2:
            self.set_font(FONTE_PADRAO, 'B', 12)
            self.set_text_color(*COR_CINZA)
            self.ln(3)
            self.cell(0, 7, texto, ln=True)
            self.set_draw_color(*COR_CINZA_CLARO)
            self.set_line_width(0.4)
            y = self.get_y()
            self.line(10, y, 200, y)
            self.ln(3)

        else:
            self.set_font(FONTE_PADRAO, 'B', 11)
            self.set_text_color(*COR_TEXTO)
            self.ln(2)
            self.cell(0, 6, texto, ln=True)
            self.ln(1)

    def texto_paragrafo(self, texto, tamanho=10, espaco_antes=1, espaco_depois=2):
        self.ln(espaco_antes)
        self.set_font(FONTE_PADRAO, '', tamanho)
        self.set_text_color(*COR_TEXTO)
        self.multi_cell(0, 5, texto)
        self.ln(espaco_depois)

    def inserir_figura(self, fig, largura=180, x=None, y=None):
        if fig is None:
            return

        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            fig.savefig(tmp.name, dpi=120, bbox_inches='tight')
            if x is None:
                x = 10
            if y is not None:
                self.image(tmp.name, x=x, w=largura, y=y)
            else:
                self.image(tmp.name, x=x, w=largura)

# ============================================================
# FUNÇÕES AUXILIARES PREMIUM
# ============================================================

def fmt_num(x):
    try:
        return f"{float(x):,.2f}"
    except:
        return str(x)

def calcular_kpis(df, coluna):
    serie = pd.to_numeric(df[coluna], errors="coerce")
    return {
        "total": serie.sum(skipna=True),
        "media": serie.mean(skipna=True),
        "mediana": serie.median(skipna=True),
        "desvio": serie.std(skipna=True),
        "minimo": serie.min(skipna=True),
        "maximo": serie.max(skipna=True),
        "cv": (serie.std(skipna=True) / serie.mean(skipna=True)) if serie.mean(skipna=True) != 0 else 0
    }

def calcular_pareto(df, coluna_cat, coluna_valor):
    df_temp = df.copy()
    df_temp[coluna_valor] = pd.to_numeric(df_temp[coluna_valor], errors="coerce")

    agrupado = df_temp.groupby(coluna_cat)[coluna_valor].sum().sort_values(ascending=False)
    total = agrupado.sum()

    acumulado = (agrupado.cumsum() / total).reset_index()
    acumulado.columns = [coluna_cat, "acumulado"]

    categorias_pareto = acumulado[acumulado["acumulado"] <= 0.80][coluna_cat].tolist()

    return agrupado, acumulado, categorias_pareto

def detectar_outliers(df, coluna):
    serie = pd.to_numeric(df[coluna], errors="coerce")

    q1 = serie.quantile(0.25)
    q3 = serie.quantile(0.75)
    iqr = q3 - q1
    limite_sup = q3 + 1.5 * iqr
    outliers_iqr = df[serie > limite_sup]

    media = serie.mean()
    desvio = serie.std()
    if desvio > 0:
        z_scores = (serie - media) / desvio
        outliers_z = df[z_scores > 3]
    else:
        outliers_z = pd.DataFrame()

    return outliers_iqr, outliers_z, limite_sup
# ============================================================
# CONTINUAÇÃO DAS FUNÇÕES AUXILIARES
# ============================================================

def calcular_correlacoes(df, numericas, coluna_alvo):
    try:
        df_num = df[numericas].apply(lambda x: pd.to_numeric(x, errors="coerce"))
        corr = df_num.corr()[coluna_alvo].sort_values(ascending=False)
        return corr.drop(coluna_alvo).head(10)
    except:
        return None

def diagnostico_qualidade(df, coluna):
    serie = df[coluna]
    nulos = serie.isna().sum()
    total = len(df)
    perc_nulos = (nulos / total * 100) if total > 0 else 0

    return {
        "nulos": nulos,
        "perc_nulos": perc_nulos
    }

def calcular_distribuicao(df, coluna):
    serie = pd.to_numeric(df[coluna], errors="coerce")
    return {
        "assimetria": serie.skew(skipna=True),
        "curtose": serie.kurtosis(skipna=True)
    }

def tabela_top10(df, coluna_valor, coluna_categoria):
    serie_val = pd.to_numeric(df[coluna_valor], errors="coerce")
    df_temp = df.copy()
    df_temp[coluna_valor] = serie_val

    top = df_temp.groupby(coluna_categoria)[coluna_valor].sum().sort_values(ascending=False).head(10)
    max_val = top.max()

    linhas = []
    for categoria, valor in top.items():
        largura = int((valor / max_val) * 30)
        barra = "█" * largura
        linhas.append([categoria, fmt_num(valor), barra])

    return linhas

def tabela_estatisticas(df, colunas_numericas):
    linhas = []
    for col in colunas_numericas:
        serie = pd.to_numeric(df[col], errors="coerce")
        linhas.append([
            col,
            fmt_num(serie.mean(skipna=True)),
            fmt_num(serie.median(skipna=True)),
            fmt_num(serie.std(skipna=True)),
            fmt_num(serie.min(skipna=True)),
            fmt_num(serie.max(skipna=True)),
        ])
    return linhas

def tabela_correlacao(df, colunas_numericas):
    df_num = df[colunas_numericas].apply(lambda x: pd.to_numeric(x, errors="coerce"))
    corr = df_num.corr()

    linhas = []
    for col in corr.columns:
        for row in corr.index:
            if col != row:
                linhas.append([row, col, f"{corr.loc[row, col]:.2f}"])

    linhas.sort(key=lambda x: abs(float(x[2])), reverse=True)
    return linhas[:15]

# ============================================================
# GRÁFICOS AVANÇADOS
# ============================================================

def fig_pareto(agrupado, acumulado, coluna_cat, coluna_valor, idx=0):
    paleta = escolher_paleta(idx)
    fig, ax1 = plt.subplots(figsize=(8, 4))

    ax1.bar(agrupado.index, agrupado.values, color=sns.color_palette(paleta, len(agrupado)))
    ax1.set_ylabel(coluna_valor)
    ax1.set_xticklabels(agrupado.index, rotation=45, ha='right')

    ax2 = ax1.twinx()
    ax2.plot(acumulado[coluna_cat], acumulado["acumulado"], color="red", marker="o")
    ax2.set_ylabel("Acumulado (%)")
    ax2.set_ylim(0, 1.05)

    plt.title("Pareto 80/20")
    plt.tight_layout()
    return fig

def fig_outliers(df, coluna, limite_sup, idx=1):
    paleta = escolher_paleta(idx)
    fig, ax = plt.subplots(figsize=(6, 4))

    sns.boxplot(
        y=pd.to_numeric(df[coluna], errors="coerce"),
        color=sns.color_palette(paleta, 3)[1],
        ax=ax
    )

    ax.axhline(limite_sup, color="red", linestyle="--", label="Limite Superior (IQR)")
    ax.legend()
    ax.set_title(f"Outliers — {coluna}")
    plt.tight_layout()
    return fig

def fig_correlacao(df, numericas, idx=2):
    paleta = escolher_paleta(idx)
    df_num = df[numericas].apply(lambda x: pd.to_numeric(x, errors="coerce"))

    fig, ax = plt.subplots(figsize=(7, 5))
    sns.heatmap(df_num.corr(), annot=True, cmap=paleta, fmt=".2f", ax=ax)
    ax.set_title("Mapa de Correlação")
    plt.tight_layout()
    return fig

def fig_sazonalidade(sazonal, idx=3):
    paleta = escolher_paleta(idx)
    fig, ax = plt.subplots(figsize=(7, 4))

    meses = list(range(1, 13))
    valores = [sazonal.get(m, 0) for m in meses]

    ax.plot(meses, valores, marker="o", color=sns.color_palette(paleta, 12)[4])
    ax.set_xticks(meses)
    ax.set_title("Sazonalidade — Média por Mês")
    ax.set_xlabel("Mês")
    ax.set_ylabel("Valor Médio")
    plt.tight_layout()
    return fig

def fig_tendencia(evolucao, idx=4):
    paleta = escolher_paleta(idx)
    fig, ax = plt.subplots(figsize=(7, 4))

    ax.plot(evolucao.index.astype(str), evolucao.values,
            marker="o", color=sns.color_palette(paleta, 12)[7])

    ax.set_title("Tendência Temporal")
    ax.set_xlabel("Período (Mês)")
    ax.set_ylabel("Total")
    plt.xticks(rotation=45)
    plt.tight_layout()
    return fig

def fig_scatter(df, coluna_x, coluna_y, idx=5):
    paleta = escolher_paleta(idx)
    fig, ax = plt.subplots(figsize=(6, 4))

    df_temp = df.copy()
    df_temp[coluna_x] = pd.to_numeric(df_temp[coluna_x], errors="coerce")
    df_temp[coluna_y] = pd.to_numeric(df_temp[coluna_y], errors="coerce")
    df_temp = df_temp.dropna(subset=[coluna_x, coluna_y])

    sns.scatterplot(
        data=df_temp,
        x=coluna_x,
        y=coluna_y,
        color=sns.color_palette(paleta, 10)[3],
        ax=ax
    )

    if len(df_temp) > 2:
        z = np.polyfit(df_temp[coluna_x], df_temp[coluna_y], 1)
        p = np.poly1d(z)
        ax.plot(df_temp[coluna_x], p(df_temp[coluna_x]), "r--")

    ax.set_title(f"Dispersão — {coluna_x} x {coluna_y}")
    plt.tight_layout()
    return fig

# ============================================================
# TABELAS AVANÇADAS PARA PDF
# ============================================================

def pdf_tabela(pdf, titulo, colunas, linhas, largura_colunas=None):
    pdf.titulo_secao(titulo, nivel=3)

    pdf.set_font(FONTE_PADRAO, 'B', 9)
    pdf.set_text_color(*COR_AZUL)

    if largura_colunas is None:
        largura_colunas = [190 / len(colunas)] * len(colunas)

    for col, w in zip(colunas, largura_colunas):
        pdf.cell(w, 7, col, border=1, align='C')
    pdf.ln()

    pdf.set_font(FONTE_PADRAO, '', 9)
    pdf.set_text_color(*COR_TEXTO)

    for linha in linhas:
        for item, w in zip(linha, largura_colunas):
            pdf.cell(w, 6, str(item), border=1)
        pdf.ln()

    pdf.ln(4)

def tabela_top10_pdf(pdf, df, coluna_valor, coluna_categoria):
    linhas = tabela_top10(df, coluna_valor, coluna_categoria)

    pdf_tabela(
        pdf,
        titulo=f"Top 10 — {coluna_categoria}",
        colunas=["Categoria", "Valor Total", "Representação"],
        linhas=linhas,
        largura_colunas=[60, 40, 90]
    )
    def tabela_estatisticas_pdf(pdf, df, colunas_numericas):
    linhas = tabela_estatisticas(df, colunas_numericas)

    pdf_tabela(
        pdf,
        titulo="Estatísticas Descritivas",
        colunas=["Coluna", "Média", "Mediana", "Desvio", "Mínimo", "Máximo"],
        linhas=linhas,
        largura_colunas=[50, 28, 28, 28, 28, 28]
    )

def tabela_correlacao_pdf(pdf, df, colunas_numericas):
    linhas = tabela_correlacao(df, colunas_numericas)

    pdf_tabela(
        pdf,
        titulo="Correlação Entre Variáveis",
        colunas=["Variável A", "Variável B", "Correlação"],
        linhas=linhas,
        largura_colunas=[60, 60, 30]
    )

def tabela_outliers_pdf(pdf, outliers_iqr, outliers_z, coluna):
    linhas = []

    for _, row in outliers_iqr.head(10).iterrows():
        linhas.append(["IQR", fmt_num(row[coluna])])

    for _, row in outliers_z.head(10).iterrows():
        linhas.append(["Z-Score", fmt_num(row[coluna])])

    if not linhas:
        linhas = [["Nenhum", "—"]]

    pdf_tabela(
        pdf,
        titulo=f"Outliers — {coluna}",
        colunas=["Método", "Valor"],
        linhas=linhas,
        largura_colunas=[40, 40]
    )

def tabela_sazonalidade_pdf(pdf, sazonal):
    linhas = []
    for mes, valor in sazonal.items():
        linhas.append([mes, fmt_num(valor)])

    pdf_tabela(
        pdf,
        titulo="Sazonalidade — Média por Mês",
        colunas=["Mês", "Valor Médio"],
        linhas=linhas,
        largura_colunas=[40, 40]
    )

def tabela_tendencia_pdf(pdf, evolucao):
    linhas = []
    for periodo, valor in evolucao.items():
        linhas.append([str(periodo), fmt_num(valor)])

    pdf_tabela(
        pdf,
        titulo="Tendência Temporal — Evolução por Mês",
        colunas=["Período", "Total"],
        linhas=linhas,
        largura_colunas=[50, 40]
    )

def tabela_qualidade_pdf(pdf, qualidade):
    linhas = [
        ["Valores Nulos", qualidade["nulos"]],
        ["% Nulos", f"{qualidade['perc_nulos']:.1f}%"]
    ]

    pdf_tabela(
        pdf,
        titulo="Qualidade dos Dados",
        colunas=["Indicador", "Valor"],
        linhas=linhas,
        largura_colunas=[60, 40]
    )

# ============================================================
# SEÇÕES DO RELATÓRIO
# ============================================================

def secao_capa(pdf, usuario):
    pdf.add_page()
    pdf.set_y(140)
    pdf.set_font(FONTE_PADRAO, 'B', 28)
    pdf.set_text_color(*COR_AZUL)
    pdf.cell(0, 12, "Relatório Executivo Completo", ln=True, align='C')

    pdf.set_font(FONTE_PADRAO, '', 14)
    pdf.set_text_color(*COR_CINZA)
    pdf.ln(4)
    pdf.cell(0, 10, f"Cliente: {usuario}", ln=True, align='C')

    pdf.ln(10)
    pdf.set_font(FONTE_PADRAO, '', 11)
    pdf.cell(0, 8, "Gerado automaticamente pelo Platero Analytics", ln=True, align='C')

def secao_sumario(pdf):
    pdf.add_page()
    pdf.titulo_secao("Sumário", nivel=1)

    secoes = [
        "1. Capa",
        "2. Sumário",
        "3. Visão Geral e KPIs",
        "4. Ranking e Distribuição",
        "5. Estatística Avançada",
        "6. Análise Temporal",
        "7. Qualidade dos Dados",
        "8. Pareto 80/20",
        "9. Outliers (IQR + Z-Score)",
        "10. Correlação, Sazonalidade e Tendência"
    ]

    pdf.set_font(FONTE_PADRAO, '', 11)
    pdf.set_text_color(*COR_TEXTO)

    for item in secoes:
        pdf.ln(4)
        pdf.cell(0, 6, item)

def secao_kpis(pdf, df, coluna_valor):
    pdf.add_page()
    pdf.titulo_secao("3. Visão Geral e KPIs", nivel=1)

    kpis = calcular_kpis(df, coluna_valor)

    pdf.texto_paragrafo(
        "Esta seção apresenta uma visão executiva dos principais indicadores "
        "da base de dados, permitindo uma leitura rápida do cenário geral."
    )

    linhas = [
        ["Total", fmt_num(kpis["total"])],
        ["Média", fmt_num(kpis["media"])],
        ["Mediana", fmt_num(kpis["mediana"])],
        ["Desvio Padrão", fmt_num(kpis["desvio"])],
        ["Coeficiente de Variação", f"{kpis['cv']*100:.1f}%"],
        ["Mínimo", fmt_num(kpis["minimo"])],
        ["Máximo", fmt_num(kpis["maximo"])]
    ]

    pdf_tabela(
        pdf,
        titulo="KPIs Principais",
        colunas=["Indicador", "Valor"],
        linhas=linhas,
        largura_colunas=[60, 40]
    )

def secao_ranking(pdf, df, coluna_cat, coluna_valor, figs_principais):
    pdf.add_page()
    pdf.titulo_secao("4. Ranking e Distribuição", nivel=1)

    pdf.texto_paragrafo(
        "Aqui analisamos a distribuição dos valores por categoria, "
        "identificando os principais grupos que concentram resultados."
    )

    tabela_top10_pdf(pdf, df, coluna_valor, coluna_cat)

    if figs_principais:
        pdf.titulo_secao("Gráfico de Distribuição", nivel=2)
        pdf.inserir_figura(figs_principais[0], largura=170)

def secao_estatistica(pdf, df, numericas):
    pdf.add_page()
    pdf.titulo_secao("5. Estatística Avançada", nivel=1)

    pdf.texto_paragrafo(
        "Nesta seção avaliamos a variabilidade, dispersão e comportamento "
        "estatístico das variáveis numéricas."
    )

    tabela_estatisticas_pdf(pdf, df, numericas)
    def secao_temporal(pdf, df, datas, coluna_valor):
    pdf.add_page()
    pdf.titulo_secao("6. Análise Temporal", nivel=1)

    if not datas:
        pdf.texto_paragrafo("Nenhuma coluna de data foi identificada na base.")
        return

    coluna_data = datas[0]

    pdf.texto_paragrafo(
        f"A análise temporal utiliza a coluna '{coluna_data}' para identificar "
        "padrões ao longo do tempo."
    )

    tendencia = calcular_tendencia(df, coluna_data, coluna_valor)
    if tendencia:
        evolucao, crescimento = tendencia

        pdf.titulo_secao("Tendência", nivel=2)
        pdf.texto_paragrafo(
            f"A tendência média mensal é de {crescimento:.1f}%. "
            "Valores positivos indicam crescimento; negativos indicam retração."
        )

        fig = fig_tendencia(evolucao)
        pdf.inserir_figura(fig, largura=170)

    sazonal = calcular_sazonalidade(df, coluna_data, coluna_valor)
    if sazonal:
        sazonalidade, mes_top = sazonal

        pdf.titulo_secao("Sazonalidade", nivel=2)
        pdf.texto_paragrafo(
            f"O mês com maior média histórica é {mes_top}. "
            "Isso pode indicar padrões sazonais relevantes."
        )

        fig = fig_sazonalidade(sazonalidade)
        pdf.inserir_figura(fig, largura=170)

def secao_qualidade(pdf, df, coluna_valor):
    pdf.add_page()
    pdf.titulo_secao("7. Qualidade dos Dados", nivel=1)

    pdf.texto_paragrafo(
        "Esta seção avalia a integridade da base, identificando valores nulos "
        "e possíveis problemas de consistência."
    )

    qualidade = diagnostico_qualidade(df, coluna_valor)
    tabela_qualidade_pdf(pdf, qualidade)

def secao_pareto(pdf, df, coluna_cat, coluna_valor):
    pdf.add_page()
    pdf.titulo_secao("8. Pareto 80/20", nivel=1)

    pdf.texto_paragrafo(
        "A análise de Pareto identifica quais categorias concentram a maior "
        "parte do resultado total."
    )

    agrupado, acumulado, categorias_pareto = calcular_pareto(df, coluna_cat, coluna_valor)

    fig = fig_pareto(agrupado, acumulado, coluna_cat, coluna_valor)
    pdf.inserir_figura(fig, largura=170)

    pdf.texto_paragrafo(
        f"As categorias que compõem 80% do total são: "
        f"{', '.join(categorias_pareto)}."
    )

    tabela_top10_pdf(pdf, df, coluna_valor, coluna_cat)

def secao_outliers(pdf, df, coluna_valor):
    pdf.add_page()
    pdf.titulo_secao("9. Outliers (IQR + Z-Score)", nivel=1)

    pdf.texto_paragrafo(
        "Outliers são valores que se afastam significativamente do padrão "
        "geral dos dados."
    )

    outliers_iqr, outliers_z, limite_sup = detectar_outliers(df, coluna_valor)

    fig = fig_outliers(df, coluna_valor, limite_sup)
    pdf.inserir_figura(fig, largura=150)

    tabela_outliers_pdf(pdf, outliers_iqr, outliers_z, coluna_valor)

    pdf.texto_paragrafo(
        "Valores acima do limite superior (IQR) ou com Z-Score acima de 3 "
        "devem ser analisados individualmente."
    )

def secao_correlacao_sazonalidade_tendencia(pdf, df, numericas, datas, coluna_valor):
    pdf.add_page()
    pdf.titulo_secao("10. Correlação, Sazonalidade e Tendência", nivel=1)

    pdf.titulo_secao("Correlação Entre Variáveis", nivel=2)
    pdf.texto_paragrafo(
        "A correlação identifica relações lineares entre variáveis numéricas."
    )

    if len(numericas) > 1:
        fig_corr = fig_correlacao(df, numericas)
        pdf.inserir_figura(fig_corr, largura=170)

        tabela_correlacao_pdf(pdf, df, numericas)

    if datas:
        coluna_data = datas[0]

        pdf.titulo_secao("Sazonalidade", nivel=2)
        sazonal = calcular_sazonalidade(df, coluna_data, coluna_valor)

        if sazonal:
            sazonalidade, mes_top = sazonal

            pdf.texto_paragrafo(
                f"O mês com maior média histórica é {mes_top}."
            )

            fig_saz = fig_sazonalidade(sazonalidade)
            pdf.inserir_figura(fig_saz, largura=170)

            tabela_sazonalidade_pdf(pdf, sazonalidade)

        pdf.titulo_secao("Tendência Temporal", nivel=2)
        tendencia = calcular_tendencia(df, coluna_data, coluna_valor)

        if tendencia:
            evolucao, crescimento = tendencia

            pdf.texto_paragrafo(
                f"A tendência média mensal é de {crescimento:.1f}%."
            )

            fig_tend = fig_tendencia(evolucao)
            pdf.inserir_figura(fig_tend, largura=170)

            tabela_tendencia_pdf(pdf, evolucao)

# ============================================================
# FUNÇÃO PRINCIPAL — GERAR PDF COMPLETO
# ============================================================

def gerar_pdf_pro(
    df_original,
    df_limpo,
    datas,
    numericas,
    categoricas,
    figs_principais,
    texto_ia,
    usuario="Cliente"
):
    pdf = PDF(orientation='P', unit='mm', format='A4')

    secao_capa(pdf, usuario)
    secao_sumario(pdf)

    coluna_valor = numericas[0]
    coluna_cat = categoricas[0] if categoricas else df_limpo.columns[0]

    secao_kpis(pdf, df_limpo, coluna_valor)
    secao_ranking(pdf, df_limpo, coluna_cat, coluna_valor, figs_principais)
    secao_estatistica(pdf, df_limpo, numericas)
    secao_temporal(pdf, df_limpo, datas, coluna_valor)
    secao_qualidade(pdf, df_limpo, coluna_valor)
    secao_pareto(pdf, df_limpo, coluna_cat, coluna_valor)
    secao_outliers(pdf, df_limpo, coluna_valor)
    secao_correlacao_sazonalidade_tendencia(pdf, df_limpo, numericas, datas, coluna_valor)

    pdf.add_page()
    pdf.titulo_secao("Parecer da Inteligência Artificial", nivel=1)

    if texto_ia:
        pdf.texto_paragrafo(texto_ia, tamanho=11)
    else:
        pdf.texto_paragrafo("Nenhuma análise adicional da IA foi fornecida.", tamanho=11)

    pdf_bytes = pdf.output(dest='S').encode('latin-1')

    import gc
    gc.collect()

    return pdf_bytes
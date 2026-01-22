# pdf_engine_pro.py

import os
import tempfile
from datetime import datetime

import pandas as pd
from fpdf import FPDF

# ================================
# CONFIGURAÇÕES GERAIS
# ================================

COR_AZUL = (0, 51, 102)
COR_CINZA = (85, 85, 85)
COR_CINZA_CLARO = (220, 220, 220)
COR_TEXTO = (40, 40, 40)
FONTE_PADRAO = "DejaVu"


# ================================
# CLASSE PDF COM DESIGN CORPORATIVO
# ================================

class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Fonte Unicode (UTF‑8)
        self.add_font("DejaVu", "", "DejaVuSans.ttf", uni=True)
        self.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf", uni=True)
        self.add_font("DejaVu", "I", "DejaVuSans-Oblique.ttf", uni=True)  # ← CORRETO

        self.set_auto_page_break(auto=True, margin=15)
        self.alias_nb_pages()

    def header(self):
        self.set_text_color(240, 240, 240)
        self.set_font(FONTE_PADRAO, 'B', 42)
        self.set_xy(0, 110)
        self.cell(0, 10, 'PLATERO ANALYTICS', align='C')

        if os.path.exists('logo.png'):
            self.image('logo.png', 10, 8, w=28)

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


# ================================
# FUNÇÕES AUXILIARES
# ================================

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

def analisar_tempo(df, coluna_data, coluna_valor):
    df_temp = df.copy()
    df_temp[coluna_data] = pd.to_datetime(df_temp[coluna_data], errors="coerce")
    df_temp[coluna_valor] = pd.to_numeric(df_temp[coluna_valor], errors="coerce")
    df_temp = df_temp.dropna(subset=[coluna_data, coluna_valor])

    df_temp["mes"] = df_temp[coluna_data].dt.to_period("M")
    agrupado = df_temp.groupby("mes")[coluna_valor].sum()

    if len(agrupado) == 0:
        return None, None, None

    crescimento = agrupado.pct_change().fillna(0)
    melhor_mes = agrupado.idxmax()
    pior_mes = agrupado.idxmin()

    return agrupado, crescimento, (melhor_mes, pior_mes)

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

def pdf_tabela(pdf, colunas, linhas, largura_total=190, altura_linha=6):
    pdf.set_font(FONTE_PADRAO, 'B', 10)
    pdf.set_fill_color(*COR_CINZA_CLARO)

    largura_col = largura_total / len(colunas)

    for col in colunas:
        pdf.cell(largura_col, altura_linha, col, border=1, align='C', fill=True)
    pdf.ln(altura_linha)

    pdf.set_font(FONTE_PADRAO, '', 9)
    pdf.set_fill_color(245, 245, 245)

    alterna = False
    for linha in linhas:
        alterna = not alterna
        for item in linha:
            pdf.cell(largura_col, altura_linha, str(item), border=1, align='C', fill=alterna)
        pdf.ln(altura_linha)


# ================================
# FUNÇÃO PRINCIPAL
# ================================

def gerar_pdf_pro(df, df_filtrado, datas, numericas, categoricas, figs, texto_ia=""):
    pdf = PDF()

    # CAPA
    pdf.add_page()
    pdf.set_font(FONTE_PADRAO, 'B', 28)
    pdf.set_text_color(*COR_AZUL)
    pdf.ln(40)
    pdf.cell(0, 15, "RELATÓRIO EXECUTIVO", ln=True, align='C')

    pdf.set_font(FONTE_PADRAO, '', 14)
    pdf.set_text_color(*COR_CINZA)
    pdf.cell(0, 10, "Análise Estratégica e Insights Avançados", ln=True, align='C')

    pdf.ln(20)
    pdf.set_font(FONTE_PADRAO, '', 12)
    pdf.set_text_color(*COR_TEXTO)
    pdf.cell(0, 8, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')

    # SUMÁRIO
    pdf.add_page()
    pdf.titulo_secao("Sumário", nivel=1)

    secoes = [
        "1. Resumo Executivo",
        "2. Ranking e Distribuição",
        "3. Análise Temporal",
        "4. Estatística Avançada",
        "5. Análise de Mercado",
        "6. Parecer da Inteligência Artificial",
        "7. Anexos"
    ]

    pdf.set_font(FONTE_PADRAO, '', 11)
    pdf.set_text_color(*COR_TEXTO)

    for secao in secoes:
        pdf.cell(0, 7, secao, ln=True)

    # SEÇÃO 1 — RESUMO EXECUTIVO
    pdf.add_page()
    pdf.titulo_secao("1. Resumo Executivo", nivel=1)

    if numericas:
        col = numericas[0]
        kpis = calcular_kpis(df, col)

        pdf.texto_paragrafo(
            "Esta seção apresenta uma visão geral dos principais indicadores "
            "extraídos da base de dados analisada."
        )

        colunas = ["Indicador", "Valor"]
        linhas = [
            ["Total Processado", fmt_num(kpis["total"])],
            ["Média", fmt_num(kpis["media"])],
            ["Mediana", fmt_num(kpis["mediana"])],
            ["Desvio Padrão", fmt_num(kpis["desvio"])],
            ["Mínimo", fmt_num(kpis["minimo"])],
            ["Máximo", fmt_num(kpis["maximo"])],
            ["Coef. Variação", fmt_num(kpis["cv"])],
        ]

        pdf_tabela(pdf, colunas, linhas)

    else:
        pdf.texto_paragrafo("Nenhuma coluna numérica foi identificada.")

    # SEÇÃO 2 — RANKING E DISTRIBUIÇÃO
    pdf.add_page()
    pdf.titulo_secao("2. Ranking e Distribuição", nivel=1)

    if numericas and categoricas:
        col_val = numericas[0]
        col_cat = categoricas[0]

        pdf.titulo_secao("Top 10 Categorias", nivel=2)
        linhas_top10 = tabela_top10(df, col_val, col_cat)
        pdf_tabela(pdf, ["Categoria", "Valor", "Escala"], linhas_top10)

        pdf.ln(5)
        pdf.titulo_secao("Gráfico de Ranking", nivel=2)

        if len(figs) > 0:
            pdf.inserir_figura(figs[0], largura=180)

    else:
        pdf.texto_paragrafo("Não há dados suficientes para gerar ranking.")

    # SEÇÃO 3 — ANÁLISE TEMPORAL
    pdf.add_page()
    pdf.titulo_secao("3. Análise Temporal", nivel=1)

    if datas and numericas:
        col_data = datas[0]
        col_val = numericas[0]

        agrupado, crescimento, extremos = analisar_tempo(df, col_data, col_val)

        if agrupado is not None:
            melhor_mes, pior_mes = extremos

            pdf.texto_paragrafo(
                "A análise temporal permite identificar tendências, sazonalidade e "
                "variações relevantes ao longo do tempo."
            )

            linhas = []
            for mes, valor in agrupado.items():
                linhas.append([str(mes), fmt_num(valor)])

            pdf.titulo_secao("Evolução Mensal", nivel=2)
            pdf_tabela(pdf, ["Mês", "Valor"], linhas)

            if len(figs) > 1:
                pdf.ln(5)
                pdf.titulo_secao("Linha do Tempo", nivel=2)
                pdf.inserir_figura(figs[1], largura=180)

            pdf.ln(5)
            pdf.titulo_secao("Crescimento Percentual", nivel=2)

            linhas_cres = []
            for mes, pct in crescimento.items():
                linhas_cres.append([str(mes), f"{pct*100:.2f}%"])

            pdf_tabela(pdf, ["Mês", "Crescimento"], linhas_cres)

            pdf.ln(5)
            pdf.titulo_secao("Melhor e Pior Período", nivel=2)
            pdf_tabela(
                pdf,
                ["Indicador", "Mês"],
                [
                    ["Melhor Mês", str(melhor_mes)],
                    ["Pior Mês", str(pior_mes)],
                ]
            )

        else:
            pdf.texto_paragrafo("Não foi possível gerar análise temporal.")
    else:
        pdf.texto_paragrafo("Não há dados suficientes para análise temporal.")

    # SEÇÃO 4 — ESTATÍSTICA AVANÇADA
    pdf.add_page()
    pdf.titulo_secao("4. Estatística Avançada", nivel=1)

    if numericas:
        pdf.titulo_secao("Estatísticas Descritivas", nivel=2)
        linhas_est = tabela_estatisticas(df, numericas)
        pdf_tabela(pdf, ["Coluna", "Média", "Mediana", "Desvio", "Mínimo", "Máximo"], linhas_est)

        if len(figs) > 3:
            pdf.ln(5)
            pdf.titulo_secao("Distribuição (Boxplot)", nivel=2)
            pdf.inserir_figura(figs[3], largura=180)

        if len(figs) > 4:
            pdf.ln(5)
            pdf.titulo_secao("Mapa de Correlação", nivel=2)
            pdf.inserir_figura(figs[4], largura=150, x=30)

        pdf.ln(5)
        pdf.titulo_secao("Top Correlações", nivel=2)
        linhas_corr = tabela_correlacao(df, numericas)
        pdf_tabela(pdf, ["Coluna A", "Coluna B", "Correlação"], linhas_corr)

    else:
        pdf.texto_paragrafo("Nenhuma coluna numérica disponível para estatísticas avançadas.")

    # SEÇÃO 5 — ANÁLISE DE MERCADO
    pdf.add_page()
    pdf.titulo_secao("5. Análise de Mercado", nivel=1)

    if len(figs) > 2:
        pdf.titulo_secao("Participação de Mercado (Top 5)", nivel=2)
        pdf.inserir_figura(figs[2], largura=150, x=30)
    else:
        pdf.texto_paragrafo("Não há dados suficientes para análise de mercado.")

    # SEÇÃO 6 — PARECER DA IA
    pdf.add_page()
    pdf.titulo_secao("6. Parecer da Inteligência Artificial", nivel=1)

    if not texto_ia:
        texto_ia = (
            "A análise automática não foi fornecida. "
            "Certifique-se de gerar o parecer antes de exportar o relatório."
        )

    pdf.texto_paragrafo(texto_ia, tamanho=11)

    # SEÇÃO 7 — ANEXOS
    pdf.add_page()
    pdf.titulo_secao("7. Anexos", nivel=1)

    pdf.texto_paragrafo(
        "Esta seção contém informações adicionais, tabelas completas e dados "
        "que podem ser úteis para análises complementares."
    )

    pdf.titulo_secao("Prévia dos Dados", nivel=2)

    preview_cols = list(df.columns)[:6]
    preview_rows = df[preview_cols].head(10).astype(str).values.tolist()

    pdf_tabela(pdf, preview_cols, preview_rows)

    # RETORNO FINAL
    return pdf.output(dest='S').encode('utf-8', errors='ignore')

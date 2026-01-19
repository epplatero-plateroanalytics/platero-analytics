import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def render_layout(df, datas, numericas, categoricas, lang="pt"):
    # --- FILTROS ---
    st.markdown("### 🛠️ Configuração da Análise")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Garante que existam opções, senão usa as colunas disponíveis
        opcoes_x = datas + categoricas
        if not opcoes_x: opcoes_x = list(df.columns)
        eixo_x = st.selectbox("Eixo X (Categoria/Tempo):", options=opcoes_x, index=0)
    
    with col2:
        if not numericas:
            st.error("Não há colunas numéricas para analisar.")
            return df
        eixo_y = st.selectbox("Eixo Y (Valor/Métrica):", options=numericas, index=0)
    
    with col3:
        top_n = st.slider("Filtrar Top N itens:", 5, 20, 10)

    # --- PROCESSAMENTO DOS DADOS (AGRUPADO) ---
    # Tenta agrupar. Se der erro de tipo, converte para string
    try:
        df_grouped = df.groupby(eixo_x)[eixo_y].sum().reset_index()
    except:
        df[eixo_x] = df[eixo_x].astype(str)
        df_grouped = df.groupby(eixo_x)[eixo_y].sum().reset_index()

    df_grouped = df_grouped.sort_values(by=eixo_y, ascending=False).head(top_n)
    
    # --- PROCESSAMENTO PARA BOXPLOT (DADOS BRUTOS) ---
    top_categorias = df_grouped[eixo_x].tolist()
    df_top_filtered = df[df[eixo_x].isin(top_categorias)]

    # --- PREPARAÇÃO PARA PDF ---
    figs_para_pdf = []

    # --- GRÁFICO 1: RANKING (BARRAS) ---
    try:
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        # Adicionado hue e legend=False para corrigir erro de versão do Seaborn
        sns.barplot(data=df_grouped, x=eixo_x, y=eixo_y, hue=eixo_x, legend=False, palette="viridis", ax=ax1)
        ax1.set_title(f"Top {top_n}: {eixo_y} por {eixo_x}")
        ax1.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        figs_para_pdf.append(fig1)
    except Exception as e:
        st.error(f"Erro ao gerar gráfico de Barras: {e}")
        fig1 = plt.figure() # Figura vazia para não quebrar
        figs_para_pdf.append(fig1)

    # --- GRÁFICO 2: EVOLUÇÃO TEMPORAL (LINHA) ---
    try:
        fig2 = None
        if eixo_x in datas:
            fig2, ax2 = plt.subplots(figsize=(8, 4))
            sns.lineplot(data=df_grouped, x=eixo_x, y=eixo_y, marker="o", color="blue", ax=ax2)
            ax2.set_title(f"Tendência Temporal: {eixo_y}")
            ax2.tick_params(axis='x', rotation=45)
            ax2.grid(True, linestyle='--', alpha=0.6)
            plt.tight_layout()
            figs_para_pdf.append(fig2)
        elif len(datas) > 0:
            col_data = datas[0]
            # Agrupa por data para evitar erros de repetição no lineplot
            df_tempo = df.groupby(col_data)[eixo_y].sum().reset_index()
            fig2, ax2 = plt.subplots(figsize=(8, 4))
            sns.lineplot(data=df_tempo, x=col_data, y=eixo_y, color="green", ax=ax2)
            ax2.set_title(f"Evolução Geral ({col_data})")
            ax2.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            figs_para_pdf.append(fig2)
    except Exception as e:
        st.warning(f"Não foi possível gerar linha do tempo: {e}")

    # --- GRÁFICO 3: PIZZA (DONUT) ---
    try:
        fig3, ax3 = plt.subplots(figsize=(6, 4))
        top_5 = df.groupby(eixo_x)[eixo_y].sum().nlargest(5)
        outros = df[eixo_y].sum() - top_5.sum()
        if outros < 0: outros = 0 # Proteção contra valores negativos
        
        dados_pizza = top_5.copy()
        dados_pizza["Outros"] = outros
        
        ax3.pie(dados_pizza, labels=dados_pizza.index, autopct='%1.1f%%', startangle=90, colors=sns.color_palette("pastel"))
        ax3.set_title(f"Share de Mercado - Top 5")
        centre_circle = plt.Circle((0,0),0.70,fc='white')
        fig3.gca().add_artist(centre_circle)
        plt.tight_layout()
        figs_para_pdf.append(fig3)
    except Exception as e:
        fig3 = plt.figure()
        figs_para_pdf.append(fig3)

    # --- GRÁFICO 4: BOXPLOT (DISTRIBUIÇÃO) ---
    # AQUI ESTAVA O ERRO PRINCIPAL
    try:
        fig4, ax4 = plt.subplots(figsize=(8, 4))
        if not df_top_filtered.empty:
            # CORREÇÃO: hue=eixo_x e legend=False
            sns.boxplot(data=df_top_filtered, x=eixo_x, y=eixo_y, hue=eixo_x, legend=False, palette="coolwarm", ax=ax4)
            ax4.set_title(f"Distribuição e Variabilidade (Boxplot)")
            ax4.tick_params(axis='x', rotation=45)
        else:
            ax4.text(0.5, 0.5, "Dados insuficientes para Boxplot", ha='center')
        plt.tight_layout()
        figs_para_pdf.append(fig4)
    except Exception as e:
        st.warning(f"Erro ao gerar Boxplot (verifique tipos de dados): {e}")
        fig4 = plt.figure()
        figs_para_pdf.append(fig4)

    # --- GRÁFICO 5: HEATMAP (CORRELAÇÃO) ---
    try:
        fig5, ax5 = plt.subplots(figsize=(6, 5))
        # Calcula correlação apenas das colunas numéricas e remove NaNs
        corr = df[numericas].corr().dropna(how='all', axis=0).dropna(how='all', axis=1)
        if not corr.empty:
            sns.heatmap(corr, annot=True, cmap="Reds", fmt=".2f", ax=ax5)
            ax5.set_title("Mapa de Calor: Correlação")
        else:
            ax5.text(0.5, 0.5, "Sem correlação calculável", ha='center')
        plt.tight_layout()
        figs_para_pdf.append(fig5)
    except Exception as e:
        fig5 = plt.figure()
        figs_para_pdf.append(fig5)

    # --- EXIBIÇÃO NA TELA ---
    st.markdown("---")
    st.subheader("📊 Análise Visual Completa")
    
    # Cria as abas. Se o gráfico 2 (linha do tempo) não existir, ajusta as abas.
    nomes_abas = ["Ranking 🏆", "Share 🍕", "Variabilidade 📦", "Correlação 🔥"]
    graficos_abas = [fig1, fig3, fig4, fig5]
    
    if fig2:
        nomes_abas.insert(1, "Tempo 📈")
        graficos_abas.insert(1, fig2)
    
    abas = st.tabs(nomes_abas)
    
    for aba, fig in zip(abas, graficos_abas):
        with aba:
            st.pyplot(fig)

    st.session_state["figs_pdf"] = figs_para_pdf
    
    return df_grouped
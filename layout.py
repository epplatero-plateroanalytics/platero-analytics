import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def render_layout(df, datas, numericas, categoricas, lang="pt"):
    # --- FILTROS ---
    st.markdown("### 🛠️ Configuração da Análise")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        eixo_x = st.selectbox("Eixo X (Categoria/Tempo):", options=datas + categoricas, index=0)
    with col2:
        eixo_y = st.selectbox("Eixo Y (Valor/Métrica):", options=numericas, index=0)
    with col3:
        top_n = st.slider("Filtrar Top N itens:", 5, 20, 10)

    # --- PROCESSAMENTO DOS DADOS (AGRUPADO) ---
    df_grouped = df.groupby(eixo_x)[eixo_y].sum().reset_index()
    df_grouped = df_grouped.sort_values(by=eixo_y, ascending=False).head(top_n)
    
    # --- PROCESSAMENTO PARA BOXPLOT (DADOS BRUTOS) ---
    # Filtra o DF original para manter apenas as categorias do Top N (para o gráfico não ficar gigante)
    top_categorias = df_grouped[eixo_x].tolist()
    df_top_filtered = df[df[eixo_x].isin(top_categorias)]

    # --- PREPARAÇÃO PARA PDF ---
    figs_para_pdf = []

    # --- GRÁFICO 1: RANKING (BARRAS) ---
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    sns.barplot(data=df_grouped, x=eixo_x, y=eixo_y, palette="viridis", ax=ax1)
    ax1.set_title(f"Top {top_n}: {eixo_y} por {eixo_x}")
    ax1.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    figs_para_pdf.append(fig1)

    # --- GRÁFICO 2: EVOLUÇÃO TEMPORAL (LINHA) ---
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
        df_tempo = df.groupby(col_data)[eixo_y].sum().reset_index()
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        sns.lineplot(data=df_tempo, x=col_data, y=eixo_y, color="green", ax=ax2)
        ax2.set_title(f"Evolução Geral ({col_data})")
        ax2.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        figs_para_pdf.append(fig2)

    # --- GRÁFICO 3: PIZZA (DONUT) ---
    fig3, ax3 = plt.subplots(figsize=(6, 4))
    top_5 = df.groupby(eixo_x)[eixo_y].sum().nlargest(5)
    outros = df[eixo_y].sum() - top_5.sum()
    dados_pizza = top_5.copy()
    dados_pizza["Outros"] = outros
    ax3.pie(dados_pizza, labels=dados_pizza.index, autopct='%1.1f%%', startangle=90, colors=sns.color_palette("pastel"))
    ax3.set_title(f"Share de Mercado - Top 5")
    centre_circle = plt.Circle((0,0),0.70,fc='white')
    fig3.gca().add_artist(centre_circle)
    plt.tight_layout()
    figs_para_pdf.append(fig3)
    
    # --- GRÁFICO 4: BOXPLOT (DISTRIBUIÇÃO) ---
    fig4, ax4 = plt.subplots(figsize=(8, 4))
    sns.boxplot(data=df_top_filtered, x=eixo_x, y=eixo_y, palette="coolwarm", ax=ax4)
    ax4.set_title(f"Distribuição e Variabilidade (Boxplot)")
    ax4.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    figs_para_pdf.append(fig4)

    # --- GRÁFICO 5: HEATMAP (CORRELAÇÃO) ---
    fig5, ax5 = plt.subplots(figsize=(6, 5))
    # Calcula correlação apenas das colunas numéricas
    corr = df[numericas].corr()
    sns.heatmap(corr, annot=True, cmap="Reds", fmt=".2f", ax=ax5)
    ax5.set_title("Mapa de Calor: Correlação")
    plt.tight_layout()
    figs_para_pdf.append(fig5)

    # --- EXIBIÇÃO NA TELA ---
    st.markdown("---")
    st.subheader("📊 Análise Visual Completa")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Ranking 🏆", "Tempo 📈", "Share 🍕", "Variabilidade 📦", "Correlação 🔥"
    ])
    
    with tab1: st.pyplot(fig1)
    with tab2: 
        if fig2: st.pyplot(fig2)
        else: st.info("Sem dados de tempo.")
    with tab3: st.pyplot(fig3)
    with tab4: 
        st.markdown("**Como ler:** A caixa mostra onde estão a maioria dos pedidos. Os pontos fora são anomalias.")
        st.pyplot(fig4)
    with tab5: 
        st.markdown("**Como ler:** Vermelho escuro = As variáveis sobem juntas (Forte relação).")
        st.pyplot(fig5)

    st.session_state["figs_pdf"] = figs_para_pdf
    
    return df_grouped
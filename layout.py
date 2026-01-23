import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def render_layout(df, datas, numericas, categoricas, lang="pt"):
    # --- FILTROS ---
    st.markdown("### 🛠️ Configuração da Análise")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Agora todas as colunas podem ser usadas como eixo X
        opcoes_x = list(df.columns)
        eixo_x = st.selectbox("Eixo X (Agrupamento):", options=opcoes_x, index=0)
    
    with col2:
        if not numericas:
            st.error("Não há colunas numéricas para analisar.")
            return df
        eixo_y = st.selectbox("Eixo Y (Métrica):", options=numericas, index=0)
    
    with col3:
        top_n = st.slider("Quantidade de Itens:", 5, 20, 10)

    # --- PROCESSAMENTO SEGURO ---
    try:
        # Não altera o df original
        df_temp = df.copy()
        df_temp[eixo_x] = df_temp[eixo_x].astype(str)

        df_grouped = df_temp.groupby(eixo_x)[eixo_y].sum().reset_index()
    except Exception as e:
        st.error(f"Erro ao processar dados: {e}")
        return df

    # Ordena do maior para o menor
    df_grouped = df_grouped.sort_values(by=eixo_y, ascending=False).head(top_n)
    
    # --- DADOS PARA O BOXPLOT ---
    top_categorias = df_grouped[eixo_x].tolist()
    df_top_filtered = df_temp[df_temp[eixo_x].isin(top_categorias)]

    figs_para_pdf = []

    # ============================================================
    # GRÁFICO 1 — BARRAS
    # ============================================================
    try:
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        sns.barplot(data=df_grouped, x=eixo_x, y=eixo_y, palette="viridis", ax=ax1)
        ax1.set_title(f"Ranking: {eixo_y} por {eixo_x}")
        ax1.tick_params(axis='x', rotation=45)

        # Rótulos nas barras
        for container in ax1.containers:
            ax1.bar_label(container, fmt='%.0f', padding=3)

        plt.tight_layout()
        figs_para_pdf.append(fig1)
    except Exception:
        fig1 = None
        figs_para_pdf.append(plt.figure())

    # ============================================================
    # GRÁFICO 2 — LINHA DO TEMPO
    # ============================================================
    fig2 = None
    try:
        # Condições para exibir gráfico temporal
        cond_tempo = (
            eixo_x in datas or
            'ANO' in str(eixo_x).upper() or
            len(datas) > 0
        )

        if cond_tempo:
            col_tempo = eixo_x if (eixo_x in datas or 'ANO' in str(eixo_x).upper()) else datas[0]

            df_tempo = df_temp.groupby(col_tempo)[eixo_y].sum().reset_index()

            fig2, ax2 = plt.subplots(figsize=(8, 4))
            sns.lineplot(data=df_tempo, x=col_tempo, y=eixo_y, marker="o", ax=ax2)
            ax2.set_title(f"Evolução: {eixo_y}")
            ax2.tick_params(axis='x', rotation=45)
            ax2.grid(True, alpha=0.3)
            plt.tight_layout()

            figs_para_pdf.append(fig2)
    except Exception:
        pass

    # ============================================================
    # GRÁFICO 3 — PIZZA
    # ============================================================
    try:
        fig3, ax3 = plt.subplots(figsize=(6, 4))
        ax3.pie(
            df_grouped[eixo_y],
            labels=df_grouped[eixo_x],
            autopct='%1.1f%%',
            startangle=90,
            colors=sns.color_palette("pastel")
        )
        ax3.set_title(f"Share Top {top_n}")
        plt.tight_layout()
        figs_para_pdf.append(fig3)
    except Exception:
        fig3 = None
        figs_para_pdf.append(plt.figure())

    # ============================================================
    # EXIBIÇÃO NA TELA
    # ============================================================
    st.markdown("---")
    st.subheader("📊 Análise Visual")
    
    abas = ["Ranking 🏆", "Share 🍕", "Evolução 📈"]
    graficos = [fig1, fig3, fig2]  # ordem das abas

    my_tabs = st.tabs(abas)
    for aba, fig in zip(my_tabs, graficos):
        with aba:
            if fig:
                st.pyplot(fig)
            else:
                st.info("Gráfico não disponível para esta seleção.")

    # Salva para PDF
    st.session_state["figs_pdf"] = figs_para_pdf

    return df_grouped
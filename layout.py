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
        top_n = st.slider("Mostrar Top N itens:", 5, 20, 10)

    # --- PROCESSAMENTO DOS DADOS ---
    # Agrupa os dados para somar os valores
    df_grouped = df.groupby(eixo_x)[eixo_y].sum().reset_index()
    
    # Ordena do maior para o menor
    df_grouped = df_grouped.sort_values(by=eixo_y, ascending=False).head(top_n)

    # --- PREPARAÇÃO PARA PDF (Lista de Figuras) ---
    figs_para_pdf = []

    # --- GRÁFICO 1: RANKING (BARRAS) ---
    fig1, ax1 = plt.subplots(figsize=(8, 4))
    sns.barplot(data=df_grouped, x=eixo_x, y=eixo_y, palette="viridis", ax=ax1)
    ax1.set_title(f"Top {top_n}: {eixo_y} por {eixo_x}")
    ax1.tick_params(axis='x', rotation=45)
    plt.tight_layout()
    figs_para_pdf.append(fig1) # Guarda na lista

    # --- GRÁFICO 2: EVOLUÇÃO TEMPORAL (LINHA) ---
    # Só gera se o usuário escolheu uma DATA no eixo X, ou se existe alguma coluna de data
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
        # Se o eixo X não é data, mas existe data na planilha, vamos criar uma evolução temporal geral
        col_data = datas[0] # Pega a primeira coluna de data
        df_tempo = df.groupby(col_data)[eixo_y].sum().reset_index()
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        sns.lineplot(data=df_tempo, x=col_data, y=eixo_y, color="green", ax=ax2)
        ax2.set_title(f"Evolução Geral no Tempo ({col_data})")
        ax2.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        figs_para_pdf.append(fig2)

    # --- GRÁFICO 3: PIZZA (DONUT) ---
    # Mostra a fatia dos Top 5 vs o Resto
    fig3, ax3 = plt.subplots(figsize=(6, 4))
    
    # Pega os top 5
    top_5 = df.groupby(eixo_x)[eixo_y].sum().nlargest(5)
    # Soma o resto
    outros = df[eixo_y].sum() - top_5.sum()
    
    # Cria dados para pizza
    dados_pizza = top_5.copy()
    dados_pizza["Outros"] = outros
    
    ax3.pie(dados_pizza, labels=dados_pizza.index, autopct='%1.1f%%', startangle=90, colors=sns.color_palette("pastel"))
    ax3.set_title(f"Representatividade (Share) - Top 5")
    
    # Transforma em Donut (círculo branco no meio)
    centre_circle = plt.Circle((0,0),0.70,fc='white')
    fig3.gca().add_artist(centre_circle)
    plt.tight_layout()
    figs_para_pdf.append(fig3)

    # --- EXIBIÇÃO NA TELA ---
    st.markdown("---")
    st.subheader("📊 Análise Visual Avançada")
    
    tab1, tab2, tab3 = st.tabs(["Ranking 🏆", "Linha do Tempo 📈", "Representatividade 🍕"])
    
    with tab1:
        st.pyplot(fig1)
    with tab2:
        if fig2:
            st.pyplot(fig2)
        else:
            st.info("Selecione uma coluna de Data para ver a linha do tempo.")
    with tab3:
        st.pyplot(fig3)

    # Salva no Session State para o PDF Engine pegar depois
    st.session_state["figs_pdf"] = figs_para_pdf
    
    return df_grouped
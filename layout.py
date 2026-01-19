import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def render_layout(df, datas, numericas, categoricas, lang="pt"):
    # --- FILTROS ---
    st.markdown("### 🛠️ Configuração da Análise")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Garante que existam opções
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

    # --- PROCESSAMENTO SEGURO ---
    try:
        # Tenta converter para string para garantir o agrupamento
        df[eixo_x] = df[eixo_x].astype(str)
        df_grouped = df.groupby(eixo_x)[eixo_y].sum().reset_index()
    except Exception as e:
        st.error(f"Erro ao processar dados: {e}")
        return df

    df_grouped = df_grouped.sort_values(by=eixo_y, ascending=False).head(top_n)
    
    # --- DADOS PARA O BOXPLOT ---
    top_categorias = df_grouped[eixo_x].tolist()
    df_top_filtered = df[df[eixo_x].isin(top_categorias)]

    figs_para_pdf = []

    # --- GRÁFICO 1: BARRAS (SIMPLIFICADO) ---
    try:
        fig1, ax1 = plt.subplots(figsize=(8, 4))
        sns.barplot(data=df_grouped, x=eixo_x, y=eixo_y, palette="viridis", ax=ax1)
        ax1.set_title(f"Ranking: {eixo_y} por {eixo_x}")
        ax1.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        figs_para_pdf.append(fig1)
    except:
        figs_para_pdf.append(plt.figure())

    # --- GRÁFICO 2: LINHA DO TEMPO ---
    try:
        fig2 = None
        # Verifica se é data ou se forçamos uma linha temporal
        if (eixo_x in datas) or (len(datas) > 0):
            col_tempo = eixo_x if eixo_x in datas else datas[0]
            df_tempo = df.groupby(col_tempo)[eixo_y].sum().reset_index()
            
            fig2, ax2 = plt.subplots(figsize=(8, 4))
            sns.lineplot(data=df_tempo, x=col_tempo, y=eixo_y, marker="o", ax=ax2)
            ax2.set_title(f"Evolução: {eixo_y}")
            ax2.tick_params(axis='x', rotation=45)
            ax2.grid(True, alpha=0.3)
            plt.tight_layout()
            figs_para_pdf.append(fig2)
    except:
        pass

    # --- GRÁFICO 3: PIZZA ---
    try:
        fig3, ax3 = plt.subplots(figsize=(6, 4))
        top_5 = df.groupby(eixo_x)[eixo_y].sum().nlargest(5)
        outros = df[eixo_y].sum() - top_5.sum()
        if outros < 0: outros = 0
        
        dados = top_5.copy()
        dados["Outros"] = outros
        
        ax3.pie(dados, labels=dados.index, autopct='%1.1f%%', startangle=90, colors=sns.color_palette("pastel"))
        ax3.set_title("Share Top 5")
        plt.tight_layout()
        figs_para_pdf.append(fig3)
    except:
        figs_para_pdf.append(plt.figure())

    # --- GRÁFICO 4: BOXPLOT (CORREÇÃO DO ERRO) ---
    try:
        fig4, ax4 = plt.subplots(figsize=(8, 4))
        # Removemos parâmetros complexos que causavam o erro 'boxprops'
        sns.boxplot(data=df_top_filtered, x=eixo_x, y=eixo_y, ax=ax4, palette="coolwarm")
        ax4.set_title("Distribuição (Boxplot)")
        ax4.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        figs_para_pdf.append(fig4)
    except Exception as e:
        # Se falhar, cria um gráfico vazio com aviso, mas NÃO TRAVA O SITE
        fig4, ax4 = plt.subplots()
        ax4.text(0.5, 0.5, "Dados insuficientes para Boxplot", ha='center')
        figs_para_pdf.append(fig4)

    # --- GRÁFICO 5: HEATMAP ---
    try:
        fig5, ax5 = plt.subplots(figsize=(6, 5))
        corr = df[numericas].corr()
        if corr.shape[0] > 1: # Só desenha se tiver mais de 1 variável
            sns.heatmap(corr, annot=True, cmap="Reds", fmt=".2f", ax=ax5)
            ax5.set_title("Correlação")
        else:
            ax5.text(0.5, 0.5, "Precisa de 2+ colunas numéricas", ha='center')
        plt.tight_layout()
        figs_para_pdf.append(fig5)
    except:
        figs_para_pdf.append(plt.figure())

    # --- EXIBIÇÃO NA TELA ---
    st.markdown("---")
    st.subheader("📊 Análise Visual")
    
    abas = ["Ranking 🏆", "Share 🍕", "Variabilidade 📦", "Correlação 🔥"]
    graficos = [fig1, fig3, fig4, fig5]
    
    if fig2:
        abas.insert(1, "Tempo 📈")
        graficos.insert(1, fig2)
    
    my_tabs = st.tabs(abas)
    for aba, fig in zip(my_tabs, graficos):
        with aba: st.pyplot(fig)

    st.session_state["figs_pdf"] = figs_para_pdf
    return df_grouped
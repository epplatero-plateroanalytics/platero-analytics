import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

def render_layout(df, datas, numericas, categoricas, lang="pt"):
    st.subheader("📊 Dashboard Interativo")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.info("Configurações do Relatório")
        # Seletores
        eixo_x = st.selectbox("Eixo X (Categorias/Tempo)", categoricas + datas + numericas)
        eixo_y = st.selectbox("Eixo Y (Valores)", numericas)
        
        # Botão que ativa a geração do PDF
        if st.button("Gerar Relatório PDF"):
            st.session_state["pdf_ready"] = True
    
    with col2:
        if eixo_x and eixo_y:
            # Criar Gráfico
            fig, ax = plt.subplots(figsize=(8, 4))
            
            # Tenta agrupar dados se tiverem muitas linhas
            df_grouped = df.groupby(eixo_x)[eixo_y].sum().reset_index().sort_values(by=eixo_y, ascending=False).head(10)
            
            sns.barplot(data=df_grouped, x=eixo_x, y=eixo_y, ax=ax, palette="viridis")
            plt.xticks(rotation=45)
            plt.title(f"Análise: {eixo_y} por {eixo_x}")
            plt.tight_layout()
            
            st.pyplot(fig)
            
            # Salvar gráfico na memória para o PDF usar depois
            st.session_state["figs_pdf"] = [fig]
            st.session_state["analise_texto"] = f"O gráfico destaca os top 10 resultados de {eixo_y} agrupados por {eixo_x}. Observa-se uma concentração de valor nos primeiros itens."
            
    return df # Retorna o dataframe caso precise ser usado
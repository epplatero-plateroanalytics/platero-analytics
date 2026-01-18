import pandas as pd
from openai import OpenAI
import streamlit as st

def analisar_com_ia(df, eixo_x, eixo_y):
    # Tenta pegar a chave de API dos segredos do Streamlit
    try:
        api_key = st.secrets["OPENAI_API_KEY"]
    except:
        return "Erro: Chave da API não configurada. Configure a OPENAI_API_KEY no Streamlit Cloud."

    client = OpenAI(api_key=api_key)

    # Prepara um resumo dos dados para a IA entender (não mandamos a planilha toda para não ficar caro)
    resumo = f"""
    Colunas analisadas: '{eixo_x}' (Tempo/Categoria) e '{eixo_y}' (Valor).
    Total acumulado de {eixo_y}: {df[eixo_y].sum():.2f}
    Média de {eixo_y}: {df[eixo_y].mean():.2f}
    Valor Máximo: {df[eixo_y].max():.2f}
    Valor Mínimo: {df[eixo_y].min():.2f}
    
    Amostra dos dados (Top 5 maiores valores):
    {df.nlargest(5, eixo_y)[[eixo_x, eixo_y]].to_string(index=False)}
    """

    # O comando para o cérebro da IA
    prompt = f"""
    Você é um Analista Sênior de Business Intelligence da 'Platero Analytics'.
    Analise os dados resumidos abaixo de um cliente e escreva um parágrafo executivo e direto.
    
    Dados:
    {resumo}
    
    Diretrizes:
    1. Não cite códigos ou termos técnicos de programação.
    2. Foque em tendências, picos e desempenho.
    3. Use linguagem profissional de negócios em Português do Brasil.
    4. Máximo de 5 linhas.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Modelo rápido e barato
            messages=[
                {"role": "system", "content": "Você é um assistente útil de análise de dados."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Não foi possível gerar a análise automática no momento. Erro: {e}"
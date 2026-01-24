import pytest
import pandas as pd
from pdf_engine_cloud import gerar_pdf_pro

def test_pdf_generation_basic():
    """Teste básico para verificar se o PDF é gerado sem erros."""
    # DataFrame simples para teste
    df = pd.DataFrame({
        "Data": pd.date_range("2024-01-01", periods=10),
        "Categoria": ["A", "B"] * 5,
        "Valor": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    })

    # Geração do PDF
    pdf_bytes = gerar_pdf_pro(
        df_original=df,
        df_limpo=df,
        datas=["Data"],
        numericas=["Valor"],
        categoricas=["Categoria"],
        figs_principais=[],
        texto_ia="Teste automático da IA",
        usuario="Teste"
    )

    # Verificações
    # FPDF2 pode retornar bytearray, então checamos ambos
    assert isinstance(pdf_bytes, (bytes, bytearray)) 
    assert len(pdf_bytes) > 1000  # PDF mínimo válido

def test_pdf_encoding_safety():
    """Teste de segurança para garantir que Emojis não quebrem o app."""
    df = pd.DataFrame({"A": [1], "B": [2]})
    
    # Texto com emoji e caracteres especiais que causavam o erro
    texto_perigoso = "Análise com emoji 📊 e aspas “inteligentes”."

    try:
        pdf_bytes = gerar_pdf_pro(
            df_original=df,
            df_limpo=df,
            datas=[],
            numericas=["A"],
            categoricas=[],
            figs_principais=[],
            texto_ia=texto_perigoso, # Aqui está o teste real
            usuario="Cliente 😎"
        )
        assert isinstance(pdf_bytes, (bytes, bytearray))
        print("Sucesso: O sistema sanitizou os caracteres especiais corretamente.")
    except Exception as e:
        pytest.fail(f"O PDF falhou ao processar caracteres especiais: {e}")
"""
Calculadora NDVI - Ponto de entrada da aplicação Streamlit.

Execute com: python main.py ou uv run python main.py
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Função principal."""
    print("🌱 Iniciando Calculadora NDVI com Streamlit...")
    print("📡 Conectando ao Microsoft Planetary Computer...")
    print("🌐 Abrindo interface no navegador...")
    print("📝 Use Ctrl+C para encerrar")
    print("-" * 50)

    # Caminho para o app Streamlit
    app_path = Path(__file__).parent / "src" / "ui" / "streamlit_app.py"

    # Executar streamlit
    subprocess.run([
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port=8501",
        "--server.address=0.0.0.0",
        "--theme.primaryColor=#00cc66",
        "--theme.backgroundColor=#0e1117",
        "--theme.secondaryBackgroundColor=#262730"
    ])


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Script de teste para verificar se a instalação está funcionando.
Execute: uv run python check_setup.py
"""

import sys
from pathlib import Path

print("🔍 Verificando instalação da Calculadora NDVI...\n")

# Verificar Python
print(f"✓ Python {sys.version.split()[0]}")

# Verificar importações
errors = []

try:
    import numpy as np
    print(f"✓ NumPy {np.__version__}")
except ImportError as e:
    errors.append(f"✗ NumPy: {e}")

try:
    import rasterio
    print(f"✓ Rasterio {rasterio.__version__}")
except ImportError as e:
    errors.append(f"✗ Rasterio: {e}")

try:
    import geopandas as gpd
    print(f"✓ GeoPandas {gpd.__version__}")
except ImportError as e:
    errors.append(f"✗ GeoPandas: {e}")

try:
    import gradio as gr
    print(f"✓ Gradio {gr.__version__}")
except ImportError as e:
    errors.append(f"✗ Gradio: {e}")

try:
    import pystac_client
    print(f"✓ PYSTAC-Client {pystac_client.__version__}")
except ImportError as e:
    errors.append(f"✗ PYSTAC-Client: {e}")

try:
    import planetary_computer as pc
    print(f"✓ Planetary Computer")
except ImportError as e:
    errors.append(f"✗ Planetary Computer: {e}")

try:
    import folium
    print(f"✓ Folium {folium.__version__}")
except ImportError as e:
    errors.append(f"✗ Folium: {e}")

try:
    import matplotlib
    print(f"✓ Matplotlib {matplotlib.__version__}")
except ImportError as e:
    errors.append(f"✗ Matplotlib: {e}")

try:
    import plotly
    print(f"✓ Plotly {plotly.__version__}")
except ImportError as e:
    errors.append(f"✗ Plotly: {e}")

# Verificar módulos do projeto
print("\n📦 Verificando módulos do projeto...")

sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from src.data.stac_client import STACClient
    print("✓ src.data.stac_client")
except ImportError as e:
    errors.append(f"✗ src.data.stac_client: {e}")

try:
    from src.processing.ndvi_calculator import NDVICalculator
    print("✓ src.processing.ndvi_calculator")
except ImportError as e:
    errors.append(f"✗ src.processing.ndvi_calculator: {e}")

try:
    from src.visualization.map_viewer import MapViewer
    print("✓ src.visualization.map_viewer")
except ImportError as e:
    errors.append(f"✗ src.visualization.map_viewer: {e}")

try:
    from src.visualization.charts import ChartCreator
    print("✓ src.visualization.charts")
except ImportError as e:
    errors.append(f"✗ src.visualization.charts: {e}")

try:
    from src.ui.gradio_app import GradioApp
    print("✓ src.ui.gradio_app")
except ImportError as e:
    errors.append(f"✗ src.ui.gradio_app: {e}")

# Verificar diretórios
print("\n📁 Verificando estrutura de diretórios...")

dirs = ["src", "tests", "data", "outputs", "examples"]
for dir_name in dirs:
    dir_path = Path(dir_name)
    if dir_path.exists():
        print(f"✓ {dir_name}/")
    else:
        errors.append(f"✗ Diretório {dir_name}/ não encontrado")

# Teste rápido de conexão STAC
print("\n🌐 Testando conexão com Microsoft Planetary Computer...")

try:
    from src.data.stac_client import STACClient
    client = STACClient(endpoint="microsoft")
    print("✓ Conexão STAC estabelecida")

    # Teste de busca simples
    bbox = (-47.95, -15.85, -47.85, -15.75)
    is_valid, msg = client.validate_bbox(bbox)
    if is_valid:
        print("✓ Validação de bbox funcionando")
    else:
        errors.append(f"✗ Validação de bbox: {msg}")

except Exception as e:
    errors.append(f"✗ Erro ao conectar STAC: {e}")

# Resultado final
print("\n" + "=" * 60)

if errors:
    print("❌ INSTALAÇÃO INCOMPLETA\n")
    print("Erros encontrados:")
    for error in errors:
        print(f"  {error}")
    print("\nExecute: uv sync")
    sys.exit(1)
else:
    print("✅ INSTALAÇÃO COMPLETA E FUNCIONAL!\n")
    print("Próximo passo:")
    print("  uv run python main.py")
    print("\nOu execute um exemplo:")
    print("  uv run python examples/example_usage.py")
    sys.exit(0)

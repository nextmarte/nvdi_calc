"""
Exemplo de uso da API do NDVI Calculator via código Python.

Execute com: uv run python examples/example_usage.py
"""

import matplotlib.pyplot as plt
from src.visualization.charts import ChartCreator
from src.visualization.map_viewer import MapViewer
from src.processing.ndvi_calculator import NDVICalculator
from src.data.stac_client import STACClient
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def example_basic_ndvi():
    """Exemplo básico de cálculo de NDVI."""
    print("=" * 60)
    print("Exemplo: Cálculo Básico de NDVI")
    print("=" * 60)

    # 1. Configurar região de interesse (Brasília, Brasil)
    bbox = (-47.95, -15.85, -47.85, -15.75)
    date_range = ("2024-01-01", "2024-12-31")

    print(f"\n📍 Região: Brasília, Brasil")
    print(f"📦 Bbox: {bbox}")
    print(f"📅 Período: {date_range[0]} até {date_range[1]}")

    # 2. Buscar imagem Sentinel-2
    print("\n🔍 Buscando imagens Sentinel-2...")
    client = STACClient(endpoint="microsoft")

    best_item = client.get_best_image(
        bbox=bbox,
        date_range=date_range,
        satellite="sentinel-2",
        max_cloud_cover=20,
    )

    if best_item is None:
        print("❌ Nenhuma imagem encontrada!")
        return

    # 3. Informações da imagem
    item_info = client.get_image_info(best_item)
    print(f"\n✅ Imagem encontrada:")
    print(f"   ID: {item_info['id']}")
    print(f"   Data: {item_info['datetime']}")
    print(f"   Nuvens: {item_info['cloud_cover']:.1f}%")
    print(f"   Plataforma: {item_info['platform']}")

    # 4. Carregar bandas
    print("\n📥 Baixando bandas...")
    band_urls = client.get_band_urls(best_item, satellite="sentinel-2")

    red_band, red_meta = NDVICalculator.load_band_from_url(
        band_urls["red"], bbox)
    nir_band, nir_meta = NDVICalculator.load_band_from_url(
        band_urls["nir"], bbox)

    print(f"   Banda Red: {red_band.shape}")
    print(f"   Banda NIR: {nir_band.shape}")

    # 5. Criar máscara de nuvens
    print("\n☁️ Criando máscara de nuvens...")
    if "scl" in band_urls:
        scl_band, _ = NDVICalculator.load_band_from_url(band_urls["scl"], bbox)
        cloud_mask = NDVICalculator.create_cloud_mask(
            scl_band, satellite="sentinel-2")
        print(f"   Pixels válidos: {cloud_mask.sum():,} / {cloud_mask.size:,}")
    else:
        cloud_mask = None
        print("   ⚠️ Máscara de nuvens não disponível")

    # 6. Calcular NDVI
    print("\n🧮 Calculando NDVI...")
    ndvi = NDVICalculator.calculate_ndvi(nir_band, red_band, cloud_mask)

    # 7. Estatísticas
    print("\n📊 Estatísticas:")
    stats = NDVICalculator.calculate_statistics(ndvi)
    print(f"   Média: {stats['mean']:.4f}")
    print(f"   Mediana: {stats['median']:.4f}")
    print(f"   Desvio Padrão: {stats['std']:.4f}")
    print(f"   Mínimo: {stats['min']:.4f}")
    print(f"   Máximo: {stats['max']:.4f}")

    # 8. Estatísticas por classe
    print("\n🌿 Distribuição de Classes:")
    class_stats = NDVICalculator.calculate_class_statistics(ndvi)
    for class_name, class_info in class_stats.items():
        print(
            f"   {class_name}: {class_info['percentage']:.2f}% ({class_info['pixel_count']:,} pixels)")

    # 9. Salvar GeoTIFF
    output_path = "outputs/example_ndvi.tif"
    NDVICalculator.save_geotiff(ndvi, output_path, red_meta)
    print(f"\n💾 NDVI salvo em: {output_path}")

    # 10. Criar visualizações
    print("\n🎨 Criando visualizações...")

    # Histograma
    fig = ChartCreator.create_histogram(
        ndvi, title="Distribuição NDVI - Exemplo")
    fig.savefig("outputs/example_histogram.png", dpi=150, bbox_inches="tight")
    print("   ✓ Histograma salvo: outputs/example_histogram.png")
    plt.close()

    # Gráfico de pizza
    fig = ChartCreator.create_class_pie_chart(
        class_stats, title="Classes de Vegetação - Exemplo")
    fig.savefig("outputs/example_pie.png", dpi=150, bbox_inches="tight")
    print("   ✓ Gráfico de pizza salvo: outputs/example_pie.png")
    plt.close()

    # Tabela de estatísticas
    fig = ChartCreator.create_statistics_table(stats, class_stats)
    fig.savefig("outputs/example_stats.png", dpi=150, bbox_inches="tight")
    print("   ✓ Tabela salva: outputs/example_stats.png")
    plt.close()

    # Mapa
    map_obj = MapViewer.create_base_map(
        center=[(-15.85 + -15.75) / 2, (-47.95 + -47.85) / 2],
        zoom=12,
    )
    map_obj = MapViewer.add_bbox_to_map(map_obj, bbox, name="ROI")
    map_obj = MapViewer.add_ndvi_overlay(
        map_obj, ndvi, bbox, palette="RdYlGn", name="NDVI")
    map_obj = MapViewer.add_legend(map_obj, palette="RdYlGn")
    map_obj.save("outputs/example_map.html")
    print("   ✓ Mapa salvo: outputs/example_map.html")

    print("\n✅ Exemplo concluído com sucesso!")
    print("=" * 60)


def example_search_images():
    """Exemplo de busca de múltiplas imagens."""
    print("\n" + "=" * 60)
    print("Exemplo: Buscar Múltiplas Imagens")
    print("=" * 60)

    bbox = (-47.95, -15.85, -47.85, -15.75)
    date_range = ("2024-06-01", "2024-08-31")

    print(f"\n📍 Região: Brasília")
    print(f"📅 Período: {date_range[0]} até {date_range[1]}")

    client = STACClient()
    items = client.search_images(
        bbox=bbox,
        date_range=date_range,
        satellite="sentinel-2",
        max_cloud_cover=30,
        limit=10,
    )

    print(f"\n✅ Encontradas {len(items)} imagens:")
    print(f"\n{'Data':<12} {'ID':<40} {'Nuvens':<10}")
    print("-" * 60)

    for item in items:
        info = client.get_image_info(item)
        date = info['datetime'][:10]
        item_id = info['id'][:40]
        clouds = info['cloud_cover']
        print(f"{date:<12} {item_id:<40} {clouds:>6.1f}%")

    print("=" * 60)


if __name__ == "__main__":
    # Criar diretório de outputs
    Path("outputs").mkdir(exist_ok=True)

    # Executar exemplos
    try:
        example_basic_ndvi()
        example_search_images()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

"""
Interface Gradio para a aplicação de cálculo NDVI.
"""

import gradio as gr
import folium
from datetime import datetime, timedelta
import numpy as np
from pathlib import Path
import tempfile
import matplotlib.pyplot as plt
import json

from ..data.stac_client import STACClient
from ..processing.ndvi_calculator import NDVICalculator
from ..visualization.map_viewer import MapViewer
from ..visualization.charts import ChartCreator
from ..config import UI_CONFIG, MAX_AREA_KM2
from .interactive_map import InteractiveMap


class GradioApp:
    """Aplicação Gradio para cálculo de NDVI."""

    def __init__(self):
        self.stac_client = STACClient()
        self.output_dir = Path("outputs")
        self.output_dir.mkdir(exist_ok=True)
        self.selected_bbox = None

    def calculate_area(self, bbox):
        """Calcula área aproximada do bbox em km²."""
        min_lon, min_lat, max_lon, max_lat = bbox
        # Aproximação simples (não considera curvatura da Terra)
        width_km = (max_lon - min_lon) * 111.32 * \
            np.cos(np.radians((min_lat + max_lat) / 2))
        height_km = (max_lat - min_lat) * 110.574
        return abs(width_km * height_km)

    def create_initial_map(self):
        """Cria mapa inicial para seleção de ROI."""
        html_content = InteractiveMap.create_selection_map()
        return html_content

    def update_coords_from_map(self, geojson_data):
        """
        Atualiza coordenadas baseado no desenho do mapa.

        Args:
            geojson_data: Dados GeoJSON do desenho

        Returns:
            Tupla com (min_lon, min_lat, max_lon, max_lat, mensagem)
        """
        if not geojson_data or geojson_data == "null" or geojson_data == "":
            return -47.95, -15.85, -47.85, -15.75, "ℹ️ Desenhe uma área no mapa ou insira coordenadas manualmente"

        bbox = InteractiveMap.extract_bbox_from_geojson(geojson_data)

        if bbox is None:
            return -47.95, -15.85, -47.85, -15.75, "⚠️ Não foi possível extrair coordenadas. Use valores padrão."

        min_lon, min_lat, max_lon, max_lat = bbox
        area_km2 = self.calculate_area(bbox)

        return min_lon, min_lat, max_lon, max_lat, f"✅ Área selecionada: {area_km2:.2f} km²"

    def process_ndvi(
        self,
        min_lon: float,
        min_lat: float,
        max_lon: float,
        max_lat: float,
        start_date: str,
        end_date: str,
        satellite: str,
        max_cloud_cover: int,
        color_palette: str,
    ):
        """
        Processa o cálculo de NDVI.

        Args:
            min_lon, min_lat, max_lon, max_lat: Coordenadas do bbox
            start_date, end_date: Datas no formato "YYYY-MM-DD"
            satellite: "sentinel-2" ou "landsat-8"
            max_cloud_cover: Cobertura máxima de nuvens (%)
            color_palette: Paleta de cores

        Returns:
            Tupla com (mapa_html, histograma, tabela_estatísticas, mensagem)
        """
        try:
            # Validar bbox
            bbox = (min_lon, min_lat, max_lon, max_lat)
            is_valid, error_msg = self.stac_client.validate_bbox(bbox)
            if not is_valid:
                return None, None, None, None, f"❌ Erro: {error_msg}"

            # Verificar área
            area_km2 = self.calculate_area(bbox)
            if area_km2 > MAX_AREA_KM2:
                return None, None, None, None, f"❌ Área muito grande ({area_km2:.1f} km²). Máximo: {MAX_AREA_KM2} km²"

            # Buscar melhor imagem
            status_msg = f"🔍 Buscando imagens {satellite}..."
            print(status_msg)

            best_item = self.stac_client.get_best_image(
                bbox=bbox,
                date_range=(start_date, end_date),
                satellite=satellite,
                max_cloud_cover=max_cloud_cover,
            )

            if best_item is None:
                return None, None, None, None, "❌ Nenhuma imagem encontrada com os critérios especificados."

            # Informações da imagem
            item_info = self.stac_client.get_image_info(best_item)
            date_str = item_info["datetime"][:10]
            cloud_cover = item_info["cloud_cover"]

            status_msg = f"✅ Imagem encontrada: {date_str} (nuvens: {cloud_cover:.1f}%)\n📥 Baixando bandas..."
            print(status_msg)

            # Obter URLs das bandas
            band_urls = self.stac_client.get_band_urls(
                best_item, satellite=satellite)

            if "red" not in band_urls or "nir" not in band_urls:
                return None, None, None, None, "❌ Erro: Bandas necessárias não encontradas."

            # Carregar bandas
            red_band, red_meta = NDVICalculator.load_band_from_url(
                band_urls["red"], bbox)
            nir_band, nir_meta = NDVICalculator.load_band_from_url(
                band_urls["nir"], bbox)

            status_msg += "\n🧮 Calculando NDVI..."
            print(status_msg)

            # Criar máscara de nuvens (se disponível)
            cloud_mask = None
            if "scl" in band_urls or "qa" in band_urls:
                mask_url = band_urls.get("scl") or band_urls.get("qa")
                mask_band, _ = NDVICalculator.load_band_from_url(
                    mask_url, bbox)
                cloud_mask = NDVICalculator.create_cloud_mask(
                    mask_band, satellite=satellite)

            # Calcular NDVI
            ndvi = NDVICalculator.calculate_ndvi(
                nir_band, red_band, cloud_mask)

            # Calcular estatísticas
            stats = NDVICalculator.calculate_statistics(ndvi)
            class_stats = NDVICalculator.calculate_class_statistics(ndvi)

            # Salvar GeoTIFF
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"ndvi_{timestamp}.tif"
            NDVICalculator.save_geotiff(ndvi, str(output_path), red_meta)

            status_msg += f"\n💾 NDVI salvo em: {output_path}"

            # Criar visualizações
            status_msg += "\n🎨 Criando visualizações..."
            print(status_msg)

            # Mapa
            map_obj = MapViewer.create_base_map(
                center=[(min_lat + max_lat) / 2, (min_lon + max_lon) / 2],
                zoom=12,
            )
            map_obj = MapViewer.add_bbox_to_map(map_obj, bbox, name="ROI")
            map_obj = MapViewer.add_ndvi_overlay(
                map_obj, ndvi, bbox, palette=color_palette, name=f"NDVI {date_str}"
            )
            map_obj = MapViewer.add_legend(map_obj, palette=color_palette)

            # Salvar mapa
            map_html_path = self.output_dir / f"map_{timestamp}.html"
            map_obj.save(str(map_html_path))

            # Histograma
            fig_hist = ChartCreator.create_histogram(
                ndvi, title=f"Distribuição NDVI - {date_str}")
            hist_path = self.output_dir / f"histogram_{timestamp}.png"
            fig_hist.savefig(hist_path, dpi=150, bbox_inches="tight")
            plt.close(fig_hist)

            # Gráfico de pizza
            fig_pie = ChartCreator.create_class_pie_chart(
                class_stats, title=f"Classes de Vegetação - {date_str}")
            pie_path = self.output_dir / f"pie_{timestamp}.png"
            fig_pie.savefig(pie_path, dpi=150, bbox_inches="tight")
            plt.close(fig_pie)

            # Tabela de estatísticas
            fig_table = ChartCreator.create_statistics_table(
                stats, class_stats)
            table_path = self.output_dir / f"stats_{timestamp}.png"
            fig_table.savefig(table_path, dpi=150, bbox_inches="tight")
            plt.close(fig_table)

            # Mensagem de sucesso
            success_msg = f"""
            ✅ **Processamento concluído com sucesso!**
            
            📅 **Data da imagem:** {date_str}
            ☁️ **Cobertura de nuvens:** {cloud_cover:.1f}%
            📊 **NDVI médio:** {stats['mean']:.4f}
            📈 **NDVI mediano:** {stats['median']:.4f}
            📏 **Área processada:** {area_km2:.2f} km²
            🖼️ **Pixels válidos:** {stats['valid_pixels']:,} / {stats['total_pixels']:,}
            
            💾 **Arquivos salvos em:** {self.output_dir}/
            """

            return str(map_html_path), str(hist_path), str(pie_path), str(table_path), success_msg

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            return None, None, None, None, f"❌ Erro ao processar: {str(e)}\n\n{error_detail}"

    def create_interface(self):
        """Cria a interface Gradio."""

        with gr.Blocks(title="🌱 Calculadora NDVI", theme=gr.themes.Soft()) as app:
            gr.Markdown("""
            # 🌱 Calculadora NDVI Profissional
            
            Calcule o **NDVI (Normalized Difference Vegetation Index)** usando dados de satélite abertos e gratuitos.
            
            ### Como usar:
            1. **🗺️ Desenhe a região de interesse no mapa** (use as ferramentas de desenho) OU insira coordenadas manualmente
            2. **📅 Escolha o período** e parâmetros de busca
            3. **🚀 Clique em "Calcular NDVI"** e aguarde o processamento
            
            ---
            """)

            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 🗺️ Seleção de Área Interativa")
                    gr.Markdown("""
                    **✨ Desenhe no mapa e as coordenadas são atualizadas automaticamente!**
                    
                    **Ferramentas no canto superior esquerdo:**
                    - 📐 **Retângulo** - Para áreas regulares
                    - ✏️ **Polígono** - Para áreas irregulares
                    - ✂️ **Editar** - Modificar formas
                    - 🗑️ **Deletar** - Remover formas
                    """)
                    
                    # Mapa interativo (usa folium via HTML)
                    with gr.Row():
                        map_html = gr.HTML(
                            value=self.create_initial_map(),
                            label="Mapa de Seleção",
                            elem_id="ndvi-map"
                        )
                    
                    # Botão para capturar área desenhada
                    # geojson_input = gr.Textbox(
                    #     label="GeoJSON (dados do desenho)",
                    #     visible=False,
                    #     interactive=True
                    # )
                    
                    # capture_btn = gr.Button("📍 Usar Área Desenhada", variant="secondary")
                    # selection_status = gr.Markdown("ℹ️ Desenhe uma área no mapa ou use coordenadas abaixo")

                    gr.Markdown("### 📍 Coordenadas")
                    gr.Markdown("""
                    ✨ **Estes campos são preenchidos automaticamente quando você desenha no mapa!**
                    
                    Ou insira manualmente. **Exemplos de regiões:**
                    - 🌳 **Brasília**: -47.95, -15.85, -47.85, -15.75
                    - 🌴 **Amazônia (Manaus)**: -60.1, -3.2, -59.9, -3.0  
                    - 🌾 **Centro-Oeste**: -54.8, -15.7, -54.6, -15.5
                    """)

                    min_lon = gr.Number(
                        label="Longitude Mínima",
                        value=-47.95,
                        precision=4,
                        info="Atualizado automaticamente ao desenhar no mapa",
                        elem_id="min_lon_input"
                    )
                    min_lat = gr.Number(
                        label="Latitude Mínima",
                        value=-15.85,
                        precision=4,
                        info="Atualizado automaticamente ao desenhar no mapa",
                        elem_id="min_lat_input"
                    )
                    max_lon = gr.Number(
                        label="Longitude Máxima",
                        value=-47.85,
                        precision=4,
                        info="Atualizado automaticamente ao desenhar no mapa",
                        elem_id="max_lon_input"
                    )
                    max_lat = gr.Number(
                        label="Latitude Máxima",
                        value=-15.75,
                        precision=4,
                        info="Atualizado automaticamente ao desenhar no mapa",
                        elem_id="max_lat_input"
                    )

                    gr.Markdown("### 📅 Período")

                    # Datas padrão: último mês
                    today = datetime.now()
                    last_month = today - timedelta(days=30)

                    start_date = gr.Textbox(
                        label="Data Inicial",
                        value=last_month.strftime("%Y-%m-%d"),
                        info="Formato: YYYY-MM-DD"
                    )
                    end_date = gr.Textbox(
                        label="Data Final",
                        value=today.strftime("%Y-%m-%d"),
                        info="Formato: YYYY-MM-DD"
                    )

                    gr.Markdown("### ⚙️ Parâmetros")

                    satellite = gr.Radio(
                        choices=["sentinel-2", "landsat-8"],
                        value="sentinel-2",
                        label="Satélite",
                        info="Sentinel-2: 10m, Landsat-8: 30m"
                    )

                    max_cloud_cover = gr.Slider(
                        minimum=0,
                        maximum=100,
                        value=20,
                        step=5,
                        label="Cobertura Máxima de Nuvens (%)",
                    )

                    color_palette = gr.Radio(
                        choices=["RdYlGn", "viridis", "Greens"],
                        value="RdYlGn",
                        label="Paleta de Cores",
                    )

                    calculate_btn = gr.Button(
                        "🚀 Calcular NDVI",
                        variant="primary",
                        size="lg"
                    )

                with gr.Column(scale=2):
                    gr.Markdown("### 📊 Resultados")

                    status_output = gr.Markdown(label="Status")

                    with gr.Tabs():
                        with gr.Tab("🗺️ Mapa"):
                            map_output = gr.HTML(label="Mapa NDVI")

                        with gr.Tab("📈 Histograma"):
                            hist_output = gr.Image(label="Distribuição NDVI")

                        with gr.Tab("🥧 Classes"):
                            pie_output = gr.Image(
                                label="Distribuição de Classes")

                        with gr.Tab("📋 Estatísticas"):
                            stats_output = gr.Image(
                                label="Tabela de Estatísticas")

            # Conectar botão
            calculate_btn.click(
                fn=self.process_ndvi,
                inputs=[
                    min_lon, min_lat, max_lon, max_lat,
                    start_date, end_date,
                    satellite, max_cloud_cover, color_palette
                ],
                outputs=[map_output, hist_output,
                         pie_output, stats_output, status_output]
            )

            gr.Markdown("""
            ---
            ### 📚 Interpretação do NDVI
            
            | Valor NDVI | Interpretação |
            |------------|---------------|
            | < 0 | Água, nuvens, neve |
            | 0 - 0.2 | Solo exposto, rochas |
            | 0.2 - 0.4 | Vegetação esparsa |
            | 0.4 - 0.6 | Vegetação moderada |
            | > 0.6 | Vegetação densa/saudável |
            
            ### 🛰️ Fontes de Dados
            - **Sentinel-2**: ESA Copernicus (10m de resolução)
            - **Landsat 8**: NASA/USGS (30m de resolução)
            - **API**: Microsoft Planetary Computer (gratuito)
            """)

        return app

    def launch(self, **kwargs):
        """Lança a aplicação."""
        app = self.create_interface()
        app.launch(**kwargs)


def main():
    """Função principal para executar a aplicação."""
    app = GradioApp()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
    )


if __name__ == "__main__":
    main()

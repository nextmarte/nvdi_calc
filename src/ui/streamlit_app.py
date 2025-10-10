"""
Interface Streamlit para Calculadora NDVI.

Características:
- Mapa interativo com seleção de área (desenho)
- Captura automática de coordenadas
- Formulário integrado com processamento NDVI
- Visualização de resultados em tabs
"""

from src.visualization.charts import ChartCreator
from src.visualization.map_viewer import MapViewer
from src.processing.ndvi_calculator import NDVICalculator
from src.data.stac_client import STACClient
import json
from typing import Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
from folium.plugins import Draw
import folium
from streamlit_folium import st_folium
import streamlit as st
import sys
from pathlib import Path

# Adicionar diretório raiz ao path para importações absolutas
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))


# Configuração da página
st.set_page_config(
    page_title="Calculadora NDVI",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)


class NDVIStreamlitApp:
    """Aplicação Streamlit para cálculo de NDVI."""

    MAX_AREA_KM2 = 500  # Área máxima em km²

    def __init__(self):
        """Inicializa a aplicação."""
        # Inicializar componentes
        self.stac_client = STACClient()
        self.ndvi_calculator = NDVICalculator()
        self.map_viewer = MapViewer()
        self.chart_creator = ChartCreator()

        # Inicializar session state
        if 'bbox' not in st.session_state:
            st.session_state.bbox = None
        if 'last_draw' not in st.session_state:
            st.session_state.last_draw = None
        if 'results' not in st.session_state:
            st.session_state.results = None

    def create_map(self, center: Tuple[float, float] = (-22.84, -43.15), zoom: int = 7) -> folium.Map:
        """
        Cria mapa Folium com ferramentas de desenho.

        Args:
            center: Coordenadas do centro (lat, lon)
            zoom: Nível de zoom

        Returns:
            Mapa Folium configurado
        """
        # Criar mapa base (centralizado no estado do RJ por padrão)
        m = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles="OpenStreetMap",
            control_scale=True
        )

        # Adicionar camadas de satélite
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Satélite',
            overlay=False,
            control=True
        ).add_to(m)

        # Configurar ferramentas de desenho
        draw = Draw(
            export=False,
            draw_options={
                'polyline': False,
                'circle': False,
                'circlemarker': False,
                'marker': False,
                'polygon': {
                    'allowIntersection': False,
                    'shapeOptions': {
                        'color': '#3388ff',
                        'fillColor': '#3388ff',
                        'fillOpacity': 0.2
                    }
                },
                'rectangle': {
                    'shapeOptions': {
                        'color': '#3388ff',
                        'fillColor': '#3388ff',
                        'fillOpacity': 0.2
                    }
                }
            },
            edit_options={
                'edit': True,
                'remove': True
            }
        )
        draw.add_to(m)

        # Ajustar o enquadramento inicial para os limites aproximados do estado do RJ
        # Bounds aproximados: (min_lon, min_lat, max_lon, max_lat)
        rj_bounds = (-44.9, -23.4, -40.7, -20.5)
        # folium espera [[min_lat, min_lon], [max_lat, max_lon]]
        m.fit_bounds([[rj_bounds[1], rj_bounds[0]],
                     [rj_bounds[3], rj_bounds[2]]])

        # Adicionar controle de camadas
        folium.LayerControl().add_to(m)

        return m

    def extract_bbox_from_draw(self, draw_data: dict) -> Optional[Tuple[float, float, float, float]]:
        """
        Extrai bounding box dos dados de desenho.

        Args:
            draw_data: Dados retornados pelo st_folium

        Returns:
            Tupla (min_lon, min_lat, max_lon, max_lat) ou None
        """
        if not draw_data or 'all_drawings' not in draw_data:
            return None

        drawings = draw_data['all_drawings']
        if not drawings or len(drawings) == 0:
            return None

        # Pegar último desenho
        last_drawing = drawings[-1]

        if 'geometry' not in last_drawing:
            return None

        geometry = last_drawing['geometry']
        coords = geometry.get('coordinates', [])

        if not coords:
            return None

        # Extrair coordenadas dependendo do tipo
        if geometry['type'] == 'Polygon':
            points = coords[0]  # Primeiro anel do polígono
        elif geometry['type'] == 'Rectangle':
            points = coords[0]
        else:
            return None

        # Calcular bbox
        lons = [p[0] for p in points]
        lats = [p[1] for p in points]

        return (min(lons), min(lats), max(lons), max(lats))

    def calculate_area_km2(self, bbox: Tuple[float, float, float, float]) -> float:
        """
        Calcula área aproximada do bbox em km².

        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)

        Returns:
            Área em km²
        """
        min_lon, min_lat, max_lon, max_lat = bbox

        # Aproximação simples (mais precisa no equador)
        lat_km = 111.32  # km por grau de latitude
        # ajustado pela latitude
        lon_km = 111.32 * abs((max_lat + min_lat) / 2)

        width_km = abs(max_lon - min_lon) * lon_km
        height_km = abs(max_lat - min_lat) * lat_km

        return width_km * height_km

    def process_ndvi(
        self,
        bbox: Tuple[float, float, float, float],
        start_date: str,
        end_date: str,
        satellite: str,
        max_cloud_cover: int,
        color_palette: str,
        max_area_km2: int = 500
    ):
        """
        Processa o cálculo de NDVI.

        Args:
            bbox: Coordenadas do bbox
            start_date, end_date: Datas no formato YYYY-MM-DD
            satellite: "sentinel-2" ou "landsat-8"
            max_cloud_cover: Cobertura máxima de nuvens (%)
            color_palette: Paleta de cores
            max_area_km2: Área máxima permitida em km²
        """
        progress_bar = st.progress(0, text="Iniciando...")

        try:
            # Validar bbox
            is_valid, error_msg = self.stac_client.validate_bbox(bbox)
            if not is_valid:
                st.error(f"❌ {error_msg}")
                return

            progress_bar.progress(10, text="Validando área...")

            # Verificar área com limite configurável
            area_km2 = self.calculate_area_km2(bbox)
            if area_km2 > max_area_km2:
                st.error(
                    f"❌ Área muito grande ({area_km2:.1f} km²). Máximo configurado: {max_area_km2} km²")
                return

            progress_bar.progress(20, text="Buscando imagens por data...")

            # Buscar melhor imagem próxima à data inicial e final
            # Começar com janela pequena e ir aumentando se não encontrar
            start_item = None
            end_item = None

            # Tentar janelas progressivamente maiores: 7, 15, 30, 90, 180 dias (6 meses)
            for window in [7, 15, 30, 90, 180]:
                if not start_item:
                    start_item = self.stac_client.get_best_near_date(
                        bbox=bbox,
                        date=start_date,
                        satellite=satellite,
                        max_cloud_cover=max_cloud_cover,
                        window_days=window,
                    )
                    if start_item:
                        start_info = self.stac_client.get_image_info(
                            start_item)
                        st.info(
                            f"📅 Data inicial: {start_info['datetime'][:10]} (±{window} dias de {start_date})")

                if not end_item:
                    end_item = self.stac_client.get_best_near_date(
                        bbox=bbox,
                        date=end_date,
                        satellite=satellite,
                        max_cloud_cover=max_cloud_cover,
                        window_days=window,
                    )
                    if end_item:
                        end_info = self.stac_client.get_image_info(end_item)
                        st.info(
                            f"📅 Data final: {end_info['datetime'][:10]} (±{window} dias de {end_date})")

                # Se encontrou ambas, parar
                if start_item and end_item:
                    break

            if not start_item and not end_item:
                st.error(
                    "❌ Nenhuma imagem encontrada nas datas selecionadas. Tente aumentar a cobertura máxima de nuvens ou selecionar outro período.")
                return

            if not start_item:
                st.warning(
                    "⚠️ Nenhuma imagem encontrada próxima à data inicial. Usando apenas data final.")

            if not end_item:
                st.warning(
                    "⚠️ Nenhuma imagem encontrada próxima à data final. Usando apenas data inicial.")

            def compute_ndvi_for_item(item):
                # Informações da imagem
                item_info = self.stac_client.get_image_info(item)
                date_str_local = item_info["datetime"][:10]
                cloud_cover_local = item_info["cloud_cover"]

                # Obter URLs das bandas
                band_urls_local = self.stac_client.get_band_urls(
                    item, satellite=satellite)

                # Carregar bandas espectrais
                nir_data_local, nir_meta_local = self.ndvi_calculator.load_band_from_url(
                    url=band_urls_local["nir"],
                    bbox=bbox
                )
                red_data_local, red_meta_local = self.ndvi_calculator.load_band_from_url(
                    url=band_urls_local["red"],
                    bbox=bbox
                )

                # Calcular NDVI
                ndvi_local = self.ndvi_calculator.calculate_ndvi(
                    nir=nir_data_local,
                    red=red_data_local
                )

                # Aplicar máscara de nuvens
                mask_key_local = "scl" if satellite == "sentinel-2" else "qa"
                if mask_key_local in band_urls_local:
                    mask_data_local, _ = self.ndvi_calculator.load_band_from_url(
                        url=band_urls_local[mask_key_local],
                        bbox=bbox
                    )
                    cloud_mask_local = self.ndvi_calculator.create_cloud_mask(
                        scl_band=mask_data_local,
                        satellite=satellite
                    )
                    if cloud_mask_local.shape != nir_data_local.shape:
                        from skimage.transform import resize
                        cloud_mask_local = resize(
                            cloud_mask_local.astype(float),
                            nir_data_local.shape,
                            order=0,
                            preserve_range=True,
                            anti_aliasing=False,
                        ) > 0.5
                        cloud_mask_local = cloud_mask_local.astype(bool)
                    ndvi_local = self.ndvi_calculator.calculate_ndvi(
                        nir=nir_data_local,
                        red=red_data_local,
                        mask_array=cloud_mask_local,
                    )

                # Estatísticas
                stats_local = self.ndvi_calculator.calculate_statistics(
                    ndvi_local)
                class_stats_local = self.ndvi_calculator.calculate_class_statistics(
                    ndvi_local)

                # Mapa NDVI
                import matplotlib.pyplot as plt
                fig_local, ax_local = plt.subplots(figsize=(12, 8))
                if color_palette == "RdYlGn":
                    cmap = plt.cm.RdYlGn
                elif color_palette == "Greens":
                    cmap = plt.cm.Greens
                elif color_palette == "YlGn":
                    cmap = plt.cm.YlGn
                else:
                    cmap = plt.cm.viridis
                im_local = ax_local.imshow(
                    ndvi_local, cmap=cmap, vmin=-1, vmax=1)
                ax_local.set_title(
                    f"NDVI - {date_str_local}", fontsize=16, fontweight='bold')
                ax_local.set_xlabel("Pixel X")
                ax_local.set_ylabel("Pixel Y")
                cbar_local = plt.colorbar(
                    im_local, ax=ax_local, fraction=0.046, pad=0.04)
                cbar_local.set_label('NDVI', rotation=270, labelpad=20)
                legend_text_local = [
                    '< 0: Água/Nuvens',
                    '0 - 0.2: Solo Exposto',
                    '0.2 - 0.4: Vegetação Esparsa',
                    '0.4 - 0.6: Vegetação Moderada',
                    '> 0.6: Vegetação Densa',
                ]
                ax_local.text(
                    1.15,
                    0.5,
                    '\n'.join(legend_text_local),
                    transform=ax_local.transAxes,
                    fontsize=10,
                    verticalalignment='center',
                    bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                )
                plt.tight_layout()

                histogram_local = self.chart_creator.create_histogram(
                    ndvi=ndvi_local, bins=50)

                return {
                    'map': fig_local,
                    'histogram': histogram_local,
                    'stats': stats_local,
                    'class_stats': class_stats_local,
                    'ndvi_data': ndvi_local,
                    'date': date_str_local,
                    'cloud_cover': cloud_cover_local,
                }

            # Computar resultados para cada data disponível
            results_start = compute_ndvi_for_item(
                start_item) if start_item else None
            progress_bar.progress(60, text="Processando data final...")
            results_end = compute_ndvi_for_item(end_item) if end_item else None

            if results_end:
                chosen = results_end
            elif results_start:
                chosen = results_start
            else:
                st.error(
                    "❌ Não foi possível processar NDVI para as datas informadas.")
                return

            progress_bar.progress(100, text="Concluído!")

            # Armazenar resultados principais e de comparação
            st.session_state.results = {
                **chosen,
                'area_km2': area_km2,
                'comparison': {
                    'start': results_start,
                    'end': results_end,
                }
            }

        except Exception as e:
            st.error(f"❌ Erro ao processar: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
        finally:
            progress_bar.empty()

    def render_sidebar(self):
        """Renderiza barra lateral com parâmetros."""
        st.sidebar.title("🌱 Calculadora NDVI")
        st.sidebar.markdown("---")

        st.sidebar.subheader("📍 Coordenadas")

        # Obter coordenadas do bbox ou usar padrão
        if st.session_state.bbox:
            min_lon, min_lat, max_lon, max_lat = st.session_state.bbox
            st.sidebar.success("✅ Área selecionada no mapa!")
        else:
            # Valores padrão (RJ - área pequena para não exceder limite de área)
            min_lon, min_lat = -43.7, -23.1
            max_lon, max_lat = -43.1, -22.7
            st.sidebar.info("ℹ️ Desenhe uma área no mapa")

        # Campos de coordenadas (podem ser editados)
        # Usar keys dinâmicas com hash do bbox para forçar atualização
        bbox_hash = hash(str(st.session_state.bbox)
                         ) if st.session_state.bbox else 0

        col1, col2 = st.sidebar.columns(2)
        with col1:
            min_lon_input = st.number_input(
                "Lon Mín",
                value=float(min_lon),
                format="%.4f",
                key=f"min_lon_{bbox_hash}"
            )
            min_lat_input = st.number_input(
                "Lat Mín",
                value=float(min_lat),
                format="%.4f",
                key=f"min_lat_{bbox_hash}"
            )
        with col2:
            max_lon_input = st.number_input(
                "Lon Máx",
                value=float(max_lon),
                format="%.4f",
                key=f"max_lon_{bbox_hash}"
            )
            max_lat_input = st.number_input(
                "Lat Máx",
                value=float(max_lat),
                format="%.4f",
                key=f"max_lat_{bbox_hash}"
            )

        bbox = (min_lon_input, min_lat_input, max_lon_input, max_lat_input)

        st.sidebar.markdown("---")
        st.sidebar.subheader("📅 Período")

        # Datas padrão: último mês
        today = datetime.now()
        last_month = today - timedelta(days=30)

        start_date = st.sidebar.date_input(
            "Data Inicial",
            value=last_month,
            max_value=today
        )
        end_date = st.sidebar.date_input(
            "Data Final",
            value=today,
            max_value=today
        )

        st.sidebar.markdown("---")
        st.sidebar.subheader("⚙️ Parâmetros")

        satellite = st.sidebar.selectbox(
            "Satélite",
            options=["sentinel-2", "landsat-8"],
            index=0,
            help="Sentinel-2: 10m, Landsat-8: 30m"
        )

        max_cloud_cover = st.sidebar.slider(
            "Cobertura máxima de nuvens (%)",
            min_value=0,
            max_value=100,
            value=20,
            step=5
        )

        max_area_km2 = st.sidebar.slider(
            "Área máxima permitida (km²)",
            min_value=10,
            max_value=2000,
            value=500,
            step=10,
            help="Limita o tamanho da área para evitar downloads muito grandes"
        )

        color_palette = st.sidebar.selectbox(
            "Paleta de cores",
            options=["RdYlGn", "Greens", "YlGn", "viridis"],
            index=0
        )

        st.sidebar.markdown("---")

        # Botão de calcular
        if st.sidebar.button("🚀 Calcular NDVI", type="primary", width='stretch'):
            self.process_ndvi(
                bbox=bbox,
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d"),
                satellite=satellite,
                max_cloud_cover=max_cloud_cover,
                color_palette=color_palette,
                max_area_km2=max_area_km2
            )

        # Informações
        st.sidebar.markdown("---")
        st.sidebar.caption(
            "💡 **Dica:** Desenhe no mapa e as coordenadas são atualizadas automaticamente!")

    def render_results(self):
        """Renderiza resultados do processamento."""
        if not st.session_state.results:
            st.info(
                "👆 Configure os parâmetros na barra lateral e clique em **Calcular NDVI**")
            return

        results = st.session_state.results

        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📅 Data", results['date'])
        with col2:
            st.metric("☁️ Nuvens", f"{results['cloud_cover']:.1f}%")
        with col3:
            st.metric("📏 Área", f"{results['area_km2']:.2f} km²")
        with col4:
            st.metric("🌱 NDVI Médio", f"{results['stats']['mean']:.3f}")

        # Tabs de resultados
        tab1, tab2, tab3, tab4 = st.tabs(
            ["🗺️ Mapa", "📊 Histograma", "📈 Estatísticas", "🪞 Comparação"])

        with tab1:
            st.pyplot(results['map'])

        with tab2:
            st.pyplot(results['histogram'])

        with tab3:
            stats = results['stats']

            # Tabela de estatísticas
            stats_df = pd.DataFrame({
                'Métrica': ['Média', 'Mediana', 'Desvio Padrão', 'Mínimo', 'Máximo'],
                'Valor': [
                    f"{stats['mean']:.4f}",
                    f"{stats['median']:.4f}",
                    f"{stats['std']:.4f}",
                    f"{stats['min']:.4f}",
                    f"{stats['max']:.4f}"
                ]
            })

            st.dataframe(stats_df, width='stretch', hide_index=True)

            # Classificação
            st.subheader("Classificação de Vegetação")

            class_colors = {
                'Água/Nuvens': '#0000ff',
                'Solo Exposto': '#8b4513',
                'Vegetação Esparsa': '#ffff00',
                'Vegetação Moderada': '#90ee90',
                'Vegetação Densa': '#006400'
            }

            # Mapear chaves internas para nomes em PT-BR
            labels_pt = {
                'water': 'Água/Nuvens',
                'bare_soil': 'Solo Exposto',
                'sparse_vegetation': 'Vegetação Esparsa',
                'moderate_vegetation': 'Vegetação Moderada',
                'dense_vegetation': 'Vegetação Densa',
            }

            class_stats = results.get('class_stats', {})
            for key, data in class_stats.items():
                class_name_pt = labels_pt.get(key, key)
                percentage = data.get('percentage', 0.0)
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(
                        f"<div style='background-color: {class_colors.get(class_name_pt, '#ccc')}; "
                        f"padding: 10px; border-radius: 5px; color: white; font-weight: bold;'>"
                        f"{class_name_pt}</div>",
                        unsafe_allow_html=True
                    )
                with col2:
                    st.metric(
                        "Percentual", f"{percentage:.1f}%", label_visibility="collapsed")

        with tab4:
            comp = results.get('comparison', {})
            start_res = comp.get('start')
            end_res = comp.get('end')

            if not start_res or not end_res:
                st.info(
                    "⚠️ Análise de comparação requer imagens em ambas as datas. Selecione um período com dados disponíveis.")
                if start_res and not end_res:
                    st.warning(
                        "✅ Data inicial disponível | ❌ Data final não encontrada")
                elif end_res and not start_res:
                    st.warning(
                        "❌ Data inicial não encontrada | ✅ Data final disponível")
            else:
                # === ANÁLISE DE MUDANÇA (DESTAQUE) ===
                st.header("📊 Análise de Mudança de Vegetação")
                st.markdown(
                    f"**Período:** {start_res['date']} → {end_res['date']}")

                import numpy as np
                import matplotlib.pyplot as plt

                # Calcular delta NDVI
                ndvi_start = start_res['ndvi_data']
                ndvi_end = end_res['ndvi_data']

                # Garantir mesmas dimensões (caso haja diferença)
                if ndvi_start.shape != ndvi_end.shape:
                    st.warning(
                        "⚠️ Dimensões diferentes entre imagens. Análise de diferença limitada.")
                    delta_ndvi = None
                else:
                    delta_ndvi = ndvi_end - ndvi_start

                if delta_ndvi is not None:
                    # Métricas de mudança
                    col1, col2, col3, col4 = st.columns(4)

                    # Calcular métricas com tratamento de NaN e arrays vazios
                    # Suprimir todos os warnings de numpy
                    import warnings
                    with warnings.catch_warnings():
                        warnings.filterwarnings(
                            'ignore', category=RuntimeWarning)
                        with np.errstate(invalid='ignore', divide='ignore'):
                            mean_change = float(np.nanmean(delta_ndvi))
                            if np.isnan(mean_change):
                                mean_change = 0.0

                            positive_change = float(np.sum(delta_ndvi > 0.1))
                            negative_change = float(np.sum(delta_ndvi < -0.1))
                            total_valid = float(np.sum(~np.isnan(delta_ndvi)))

                    pct_gain = (positive_change / total_valid *
                                100) if total_valid > 0 else 0
                    pct_loss = (negative_change / total_valid *
                                100) if total_valid > 0 else 0

                    with col1:
                        delta_emoji = "📈" if mean_change > 0 else "📉" if mean_change < 0 else "➡️"
                        st.metric("Mudança Média",
                                  f"{mean_change:+.3f}", delta_emoji)
                    with col2:
                        st.metric("🌱 Ganho de Vegetação", f"{pct_gain:.1f}%",
                                  help="Pixels com aumento > 0.1 no NDVI")
                    with col3:
                        st.metric("🔥 Perda de Vegetação", f"{pct_loss:.1f}%",
                                  help="Pixels com redução > 0.1 no NDVI")
                    with col4:
                        mean_start = start_res['stats'].get('mean')
                        mean_end = end_res['stats'].get('mean')

                        if mean_start is not None and mean_end is not None and mean_start != 0:
                            pct_change = (mean_end - mean_start) / \
                                abs(mean_start) * 100
                        else:
                            pct_change = 0.0

                        st.metric("Variação NDVI Médio", f"{pct_change:+.1f}%")

                    st.markdown("---")

                    # Mapa de diferença (destaque visual)
                    st.subheader("🗺️ Mapa de Mudança (Delta NDVI)")

                    fig_delta, ax_delta = plt.subplots(figsize=(14, 9))

                    # Colormap divergente: vermelho (perda) → branco (sem mudança) → verde (ganho)
                    im_delta = ax_delta.imshow(
                        delta_ndvi, cmap='RdYlGn', vmin=-0.5, vmax=0.5)
                    ax_delta.set_title(
                        f"Mudança de NDVI ({start_res['date']} → {end_res['date']})",
                        fontsize=18, fontweight='bold'
                    )
                    ax_delta.set_xlabel("Pixel X", fontsize=12)
                    ax_delta.set_ylabel("Pixel Y", fontsize=12)

                    cbar_delta = plt.colorbar(
                        im_delta, ax=ax_delta, fraction=0.046, pad=0.04)
                    cbar_delta.set_label(
                        'Variação NDVI', rotation=270, labelpad=25, fontsize=12)

                    # Legenda interpretativa (sem emojis para evitar warnings de fonte)
                    legend_delta = [
                        '< -0.2: Perda severa',
                        '-0.2 a -0.1: Perda moderada',
                        '-0.1 a +0.1: Sem mudança',
                        '+0.1 a +0.2: Ganho moderado',
                        '> +0.2: Ganho acentuado'
                    ]
                    ax_delta.text(
                        1.18, 0.5, '\n'.join(legend_delta),
                        transform=ax_delta.transAxes,
                        fontsize=11,
                        verticalalignment='center',
                        bbox=dict(boxstyle='round',
                                  facecolor='lightgray', alpha=0.8)
                    )

                    plt.tight_layout()
                    st.pyplot(fig_delta)

                    st.markdown("---")

                    # Comparação de estatísticas por classe
                    st.subheader("📈 Mudança por Classe de Vegetação")

                    labels_pt = {
                        'water': 'Água/Nuvens',
                        'bare_soil': 'Solo Exposto',
                        'sparse_vegetation': 'Vegetação Esparsa',
                        'moderate_vegetation': 'Vegetação Moderada',
                        'dense_vegetation': 'Vegetação Densa',
                    }

                    class_comparison = []
                    for key in labels_pt.keys():
                        start_pct = start_res['class_stats'].get(
                            key, {}).get('percentage', 0)
                        end_pct = end_res['class_stats'].get(
                            key, {}).get('percentage', 0)
                        change = end_pct - start_pct
                        class_comparison.append({
                            'Classe': labels_pt[key],
                            'Início (%)': f"{start_pct:.1f}",
                            'Fim (%)': f"{end_pct:.1f}",
                            'Variação (p.p.)': f"{change:+.1f}"
                        })

                    df_comparison = pd.DataFrame(class_comparison)
                    st.dataframe(df_comparison, width='stretch',
                                 hide_index=True)

                st.markdown("---")
                st.markdown("### 🔍 Comparação Detalhada Lado a Lado")

                # Imagens lado a lado para contexto
                col_left, col_right = st.columns(2)

                with col_left:
                    st.subheader(f"📅 Início: {start_res['date']}")
                    st.pyplot(start_res['map'])

                    # Tratar valores None em cloud_cover e mean
                    cloud_start = start_res.get('cloud_cover', 0)
                    mean_start_val = start_res.get('stats', {}).get('mean', 0)

                    if cloud_start is None:
                        cloud_start = 0
                    if mean_start_val is None:
                        mean_start_val = 0

                    st.caption(
                        f"☁️ Nuvens: {cloud_start:.1f}% | 🌱 NDVI Médio: {mean_start_val:.3f}")

                with col_right:
                    st.subheader(f"📅 Fim: {end_res['date']}")
                    st.pyplot(end_res['map'])

                    # Tratar valores None em cloud_cover e mean
                    cloud_end = end_res.get('cloud_cover', 0)
                    mean_end_val = end_res.get('stats', {}).get('mean', 0)

                    if cloud_end is None:
                        cloud_end = 0
                    if mean_end_val is None:
                        mean_end_val = 0

                    st.caption(
                        f"☁️ Nuvens: {cloud_end:.1f}% | 🌱 NDVI Médio: {mean_end_val:.3f}")

                # Histogramas lado a lado
                st.markdown("---")
                st.subheader("📊 Distribuição de NDVI")
                col_hist1, col_hist2 = st.columns(2)
                with col_hist1:
                    st.pyplot(start_res['histogram'])
                with col_hist2:
                    st.pyplot(end_res['histogram'])

    def run(self):
        """Executa a aplicação."""
        # Barra lateral
        self.render_sidebar()

        # Conteúdo principal
        st.title("🌱 Calculadora NDVI")
        st.markdown("### Análise de vegetação usando dados de satélite abertos")

        # Instruções
        with st.expander("ℹ️ Como usar", expanded=False):
            st.markdown("""
            **Passo a passo:**
            
            1. 🗺️ **Desenhe** uma área no mapa usando as ferramentas no canto superior esquerdo
                - 📐 Retângulo para áreas regulares
                - ✏️ Polígono para áreas irregulares
            
            2. 📍 **As coordenadas** são atualizadas automaticamente na barra lateral
            
            3. ⚙️ **Configure** os parâmetros (datas, satélite, etc.)
            
            4. 🚀 **Clique** em "Calcular NDVI" e aguarde o processamento
            
            ---
            
            **O que é NDVI?**
            
            O NDVI (Normalized Difference Vegetation Index) é um indicador que mede a saúde da vegetação:
            - 📊 Valores: -1 a +1
            - 🌊 < 0: Água, nuvens
            - 🪨 0 - 0.2: Solo exposto
            - 🌾 0.2 - 0.4: Vegetação esparsa
            - 🌳 0.4 - 0.6: Vegetação moderada
            - 🌲 > 0.6: Vegetação densa/saudável
            """)

        # Mapa
        st.subheader("🗺️ Selecione a Área de Interesse")

        # Criar mapa
        m = self.create_map()

        # Renderizar mapa e capturar desenhos
        map_data = st_folium(
            m,
            width=None,
            height=500,
            returned_objects=["all_drawings"],
            key="map"
        )

        # Debug: mostrar dados do mapa
        if map_data:
            with st.expander("🐛 Debug - Dados do mapa", expanded=False):
                st.json(map_data)

        # Extrair bbox do desenho
        if map_data and map_data.get('all_drawings'):
            bbox = self.extract_bbox_from_draw(map_data)
            if bbox:
                st.success(f"📍 Coordenadas capturadas: {bbox}")
                if bbox != st.session_state.bbox:
                    st.session_state.bbox = bbox
                    st.rerun()

        st.markdown("---")

        # Resultados
        self.render_results()


def main():
    """Função principal."""
    app = NDVIStreamlitApp()
    app.run()


if __name__ == "__main__":
    main()

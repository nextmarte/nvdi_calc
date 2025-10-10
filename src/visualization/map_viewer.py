"""
Visualizador de mapas interativos com NDVI.
"""

from typing import Optional, Tuple, List
import numpy as np
import folium
from folium import plugins
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from PIL import Image
import io
import base64

from ..config import UI_CONFIG, NDVI_CLASSES


class MapViewer:
    """Classe para criar visualizações de mapas interativos."""

    @staticmethod
    def create_base_map(
        center: Optional[List[float]] = None,
        zoom: int = 10,
        height: int = 600,
    ) -> folium.Map:
        """
        Cria um mapa base interativo.

        Args:
            center: [latitude, longitude] do centro do mapa
            zoom: Nível de zoom inicial
            height: Altura do mapa em pixels

        Returns:
            Objeto folium.Map
        """
        if center is None:
            center = UI_CONFIG["default_center"]

        m = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles="OpenStreetMap",
            height=height,
        )

        # Adicionar controle de layers
        folium.LayerControl().add_to(m)

        # Adicionar ferramentas de desenho
        draw = plugins.Draw(
            export=True,
            filename="roi.geojson",
            position="topleft",
            draw_options={
                "polyline": False,
                "rectangle": True,
                "polygon": True,
                "circle": False,
                "marker": False,
                "circlemarker": False,
            },
        )
        draw.add_to(m)

        # Adicionar medição de distância
        plugins.MeasureControl(position="topleft").add_to(m)

        # Adicionar minimap
        plugins.MiniMap().add_to(m)

        return m

    @staticmethod
    def add_bbox_to_map(
        map_obj: folium.Map,
        bbox: Tuple[float, float, float, float],
        name: str = "ROI",
        color: str = "red",
    ) -> folium.Map:
        """
        Adiciona um bounding box ao mapa.

        Args:
            map_obj: Objeto folium.Map
            bbox: (min_lon, min_lat, max_lon, max_lat)
            name: Nome da camada
            color: Cor da borda

        Returns:
            Mapa atualizado
        """
        min_lon, min_lat, max_lon, max_lat = bbox

        # Criar retângulo
        bounds = [[min_lat, min_lon], [max_lat, max_lon]]
        folium.Rectangle(
            bounds=bounds,
            color=color,
            fill=False,
            weight=2,
            popup=name,
        ).add_to(map_obj)

        # Centralizar mapa no bbox
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        map_obj.location = [center_lat, center_lon]

        return map_obj

    @staticmethod
    def create_ndvi_colormap(palette: str = "RdYlGn") -> mcolors.Colormap:
        """
        Cria um colormap para visualização NDVI.

        Args:
            palette: Nome da paleta ("RdYlGn", "viridis", "Greens")

        Returns:
            Colormap do matplotlib
        """
        if palette == "RdYlGn":
            # Vermelho-Amarelo-Verde (clássico para NDVI)
            return plt.cm.RdYlGn
        elif palette == "viridis":
            return plt.cm.viridis
        elif palette == "Greens":
            return plt.cm.Greens
        else:
            return plt.cm.RdYlGn

    @staticmethod
    def ndvi_to_rgb(
        ndvi: np.ndarray,
        palette: str = "RdYlGn",
        vmin: float = -1.0,
        vmax: float = 1.0,
    ) -> np.ndarray:
        """
        Converte array NDVI para imagem RGB.

        Args:
            ndvi: Array com valores NDVI
            palette: Nome da paleta de cores
            vmin: Valor mínimo para escala de cores
            vmax: Valor máximo para escala de cores

        Returns:
            Array RGB (height, width, 3) com valores 0-255
        """
        # Normalizar NDVI para 0-1
        ndvi_norm = np.clip((ndvi - vmin) / (vmax - vmin), 0, 1)

        # Substituir NaN por valor transparente (será tratado depois)
        ndvi_norm = np.nan_to_num(ndvi_norm, nan=0.0)

        # Aplicar colormap
        cmap = MapViewer.create_ndvi_colormap(palette)
        rgb = cmap(ndvi_norm)

        # Converter para 0-255
        rgb_uint8 = (rgb[:, :, :3] * 255).astype(np.uint8)

        # Adicionar transparência onde havia NaN
        mask = np.isnan(ndvi)
        if mask.any():
            # Criar canal alpha
            alpha = np.where(mask, 0, 255).astype(np.uint8)
            rgb_rgba = np.dstack([rgb_uint8, alpha])
            return rgb_rgba

        return rgb_uint8

    @staticmethod
    def add_ndvi_overlay(
        map_obj: folium.Map,
        ndvi: np.ndarray,
        bbox: Tuple[float, float, float, float],
        palette: str = "RdYlGn",
        opacity: float = 0.7,
        name: str = "NDVI",
    ) -> folium.Map:
        """
        Adiciona uma camada NDVI ao mapa.

        Args:
            map_obj: Objeto folium.Map
            ndvi: Array com valores NDVI
            bbox: (min_lon, min_lat, max_lon, max_lat)
            palette: Paleta de cores
            opacity: Opacidade da camada (0-1)
            name: Nome da camada

        Returns:
            Mapa atualizado
        """
        # Converter NDVI para RGB
        rgb = MapViewer.ndvi_to_rgb(ndvi, palette=palette)

        # Converter para imagem PIL
        img = Image.fromarray(rgb)

        # Converter para base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        # Adicionar ao mapa como ImageOverlay
        min_lon, min_lat, max_lon, max_lat = bbox
        bounds = [[min_lat, min_lon], [max_lat, max_lon]]

        folium.raster_layers.ImageOverlay(
            image=f"data:image/png;base64,{img_base64}",
            bounds=bounds,
            opacity=opacity,
            name=name,
            interactive=True,
        ).add_to(map_obj)

        return map_obj

    @staticmethod
    def create_legend_html(palette: str = "RdYlGn") -> str:
        """
        Cria HTML para legenda do NDVI.

        Args:
            palette: Paleta de cores usada

        Returns:
            String HTML para legenda
        """
        legend_html = """
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; width: 200px; height: auto; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px">
        <p style="margin-bottom: 5px; font-weight: bold;">NDVI Classes</p>
        """

        colors = {
            "water": "#d73027",
            "bare_soil": "#fc8d59",
            "sparse_vegetation": "#fee08b",
            "moderate_vegetation": "#d9ef8b",
            "dense_vegetation": "#1a9850",
        }

        labels = {
            "water": "Água/Nuvens (< 0)",
            "bare_soil": "Solo Exposto (0-0.2)",
            "sparse_vegetation": "Veg. Esparsa (0.2-0.4)",
            "moderate_vegetation": "Veg. Moderada (0.4-0.6)",
            "dense_vegetation": "Veg. Densa (> 0.6)",
        }

        for class_name in NDVI_CLASSES.keys():
            color = colors.get(class_name, "#cccccc")
            label = labels.get(class_name, class_name)
            legend_html += f"""
            <p style="margin: 3px 0;">
                <span style="background-color: {color}; width: 20px; height: 15px; 
                             display: inline-block; border: 1px solid #000;"></span>
                {label}
            </p>
            """

        legend_html += "</div>"
        return legend_html

    @staticmethod
    def add_legend(map_obj: folium.Map, palette: str = "RdYlGn") -> folium.Map:
        """
        Adiciona legenda ao mapa.

        Args:
            map_obj: Objeto folium.Map
            palette: Paleta de cores usada

        Returns:
            Mapa atualizado
        """
        legend_html = MapViewer.create_legend_html(palette)
        map_obj.get_root().html.add_child(folium.Element(legend_html))
        return map_obj

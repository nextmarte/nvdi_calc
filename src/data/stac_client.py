"""
Cliente STAC para buscar dados de satélite (Sentinel-2 e Landsat) via APIs abertas.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import planetary_computer as pc
from pystac_client import Client
from pystac import Item, ItemCollection

from ..config import STAC_ENDPOINTS, DEFAULT_CLOUD_COVER_MAX, SATELLITE_CONFIG


class STACClient:
    """Cliente para buscar imagens de satélite via STAC API."""

    def __init__(self, endpoint: str = "microsoft"):
        """
        Inicializa o cliente STAC.

        Args:
            endpoint: Nome do endpoint STAC ("microsoft" ou "element84")
        """
        self.endpoint = STAC_ENDPOINTS.get(
            endpoint, STAC_ENDPOINTS["microsoft"])
        self.catalog = Client.open(self.endpoint)

    def search_images(
        self,
        bbox: Tuple[float, float, float, float],
        date_range: Tuple[str, str],
        satellite: str = "sentinel-2",
        max_cloud_cover: int = DEFAULT_CLOUD_COVER_MAX,
        limit: int = 10,
    ) -> ItemCollection:
        """
        Busca imagens de satélite na região e período especificados.

        Args:
            bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
            date_range: Tupla com (data_inicial, data_final) em formato "YYYY-MM-DD"
            satellite: "sentinel-2" ou "landsat-8"
            max_cloud_cover: Cobertura máxima de nuvens em % (0-100)
            limit: Número máximo de resultados

        Returns:
            ItemCollection com as imagens encontradas

        Example:
            >>> client = STACClient()
            >>> bbox = (-48.0, -16.0, -47.5, -15.5)
            >>> items = client.search_images(
            ...     bbox=bbox,
            ...     date_range=("2024-01-01", "2024-12-31"),
            ...     satellite="sentinel-2",
            ...     max_cloud_cover=20
            ... )
        """
        # Obter configuração do satélite
        sat_config = SATELLITE_CONFIG.get(satellite)
        if not sat_config:
            raise ValueError(f"Satélite não suportado: {satellite}")

        collection = sat_config["collection"]

        # Construir data range para STAC
        datetime_str = f"{date_range[0]}/{date_range[1]}"

        # Realizar busca
        search = self.catalog.search(
            collections=[collection],
            bbox=bbox,
            datetime=datetime_str,
            query={"eo:cloud_cover": {"lt": max_cloud_cover}},
            limit=limit,
        )

        items = list(search.items())

        # Assinar URLs com Planetary Computer (necessário para download)
        if "planetarycomputer" in self.endpoint:
            items = [pc.sign(item) for item in items]

        return ItemCollection(items)

    def get_best_image(
        self,
        bbox: Tuple[float, float, float, float],
        date_range: Tuple[str, str],
        satellite: str = "sentinel-2",
        max_cloud_cover: int = DEFAULT_CLOUD_COVER_MAX,
    ) -> Optional[Item]:
        """
        Retorna a melhor imagem (menor cobertura de nuvens) no período.

        Args:
            bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
            date_range: Tupla com (data_inicial, data_final)
            satellite: "sentinel-2" ou "landsat-8"
            max_cloud_cover: Cobertura máxima de nuvens em %

        Returns:
            Item STAC da melhor imagem ou None se não encontrar
        """
        items = self.search_images(
            bbox=bbox,
            date_range=date_range,
            satellite=satellite,
            max_cloud_cover=max_cloud_cover,
            limit=50,
        )

        if not items:
            return None

        # Ordenar por cobertura de nuvens (menor primeiro)
        sorted_items = sorted(
            items,
            key=lambda item: item.properties.get("eo:cloud_cover", 100),
        )

        return sorted_items[0] if sorted_items else None

    def get_best_near_date(
        self,
        bbox: Tuple[float, float, float, float],
        date: str,
        satellite: str = "sentinel-2",
        max_cloud_cover: int = DEFAULT_CLOUD_COVER_MAX,
        window_days: int = 7,
    ) -> Optional[Item]:
        """
        Retorna a melhor imagem (menor cobertura de nuvens) em uma janela ao redor de uma data.

        Args:
            bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
            date: Data alvo no formato "YYYY-MM-DD"
            satellite: "sentinel-2" ou "landsat-8"
            max_cloud_cover: Cobertura máxima de nuvens em %
            window_days: Tamanho da janela em dias para cada lado da data

        Returns:
            Item STAC da melhor imagem próximo à data ou None se não encontrar
        """
        try:
            center = datetime.fromisoformat(date)
        except ValueError:
            # Caso a data venha inválida, retorna None
            return None

        start = (center - timedelta(days=window_days)).date().isoformat()
        end = (center + timedelta(days=window_days)).date().isoformat()

        return self.get_best_image(
            bbox=bbox,
            date_range=(start, end),
            satellite=satellite,
            max_cloud_cover=max_cloud_cover,
        )

    def get_image_info(self, item: Item) -> Dict[str, Any]:
        """
        Extrai informações úteis de um item STAC.

        Args:
            item: Item STAC

        Returns:
            Dicionário com informações da imagem
        """
        return {
            "id": item.id,
            "datetime": item.properties.get("datetime"),
            "cloud_cover": item.properties.get("eo:cloud_cover", 0),
            "platform": item.properties.get("platform", ""),
            "instruments": item.properties.get("instruments", []),
            "bbox": item.bbox,
            "assets": list(item.assets.keys()),
        }

    def get_band_urls(
        self, item: Item, satellite: str = "sentinel-2"
    ) -> Dict[str, str]:
        """
        Obtém URLs das bandas necessárias para calcular NDVI.

        Args:
            item: Item STAC
            satellite: "sentinel-2" ou "landsat-8"

        Returns:
            Dicionário com URLs das bandas (red, nir, scl/qa)
        """
        sat_config = SATELLITE_CONFIG.get(satellite)
        if not sat_config:
            raise ValueError(f"Satélite não suportado: {satellite}")

        bands = sat_config["bands"]
        urls: Dict[str, str] = {}

        def try_keys(keys: List[str]) -> Optional[str]:
            for k in keys:
                if k in item.assets:
                    return item.assets[k].href
            return None

        for band_type, band_name in bands.items():
            href: Optional[str] = None

            # Primeiro, tente o nome exato configurado
            if band_name in item.assets:
                href = item.assets[band_name].href
            else:
                # Nomes alternativos por satélite
                alt_keys: List[str] = []
                if satellite == "sentinel-2":
                    if band_type == "red":
                        alt_keys = ["red", "B04"]
                    elif band_type == "nir":
                        alt_keys = ["nir", "B08"]
                    elif band_type == "scl":
                        alt_keys = ["SCL", "scl"]
                elif satellite == "landsat-8":
                    # Landsat Collection 2 Level-2 geralmente usa SR_B4/SR_B5
                    if band_type == "red":
                        alt_keys = ["SR_B4", "B4", "red"]
                    elif band_type == "nir":
                        alt_keys = ["SR_B5", "B5", "nir"]
                    elif band_type == "qa":
                        alt_keys = ["QA_PIXEL", "SR_QA_PIXEL", "qa_pixel"]

                href = try_keys(alt_keys)

            if href:
                urls[band_type] = href

        return urls

    def validate_bbox(
        self, bbox: Tuple[float, float, float, float]
    ) -> Tuple[bool, str]:
        """
        Valida se o bounding box é válido.

        Args:
            bbox: (min_lon, min_lat, max_lon, max_lat)

        Returns:
            Tupla (é_válido, mensagem_erro)
        """
        min_lon, min_lat, max_lon, max_lat = bbox

        if min_lon >= max_lon:
            return False, "Longitude mínima deve ser menor que longitude máxima"

        if min_lat >= max_lat:
            return False, "Latitude mínima deve ser menor que latitude máxima"

        if not (-180 <= min_lon <= 180) or not (-180 <= max_lon <= 180):
            return False, "Longitude deve estar entre -180 e 180"

        if not (-90 <= min_lat <= 90) or not (-90 <= max_lat <= 90):
            return False, "Latitude deve estar entre -90 e 90"

        return True, ""

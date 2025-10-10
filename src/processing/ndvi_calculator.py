"""
Calculadora de NDVI (Normalized Difference Vegetation Index).
"""

from typing import Optional, Tuple

import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
import xarray as xr
from shapely.geometry import shape

from ..config import NDVI_CLASSES


class NDVICalculator:
    """Classe para calcular NDVI a partir de bandas espectrais."""

    @staticmethod
    def calculate_ndvi(
        nir: np.ndarray, red: np.ndarray, mask_array: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Calcula NDVI usando as bandas NIR e Red.

        Fórmula: NDVI = (NIR - Red) / (NIR + Red)

        Args:
            nir: Array com banda Near Infrared (NIR)
            red: Array com banda Red
            mask_array: Máscara booleana opcional (True = válido, False = inválido)

        Returns:
            Array com valores NDVI (-1 a +1)

        Example:
            >>> nir = np.array([[800, 850], [900, 820]])
            >>> red = np.array([[100, 120], [110, 105]])
            >>> ndvi = NDVICalculator.calculate_ndvi(nir, red)
        """
        # Converter para float para evitar overflow
        nir = nir.astype(np.float32)
        red = red.astype(np.float32)

        # Calcular NDVI com tratamento de divisão por zero e inválidos
        numerator = nir - red
        denominator = nir + red

        with np.errstate(divide='ignore', invalid='ignore'):
            ndvi = np.divide(numerator, denominator, out=np.full_like(
                numerator, np.nan, dtype=np.float32), where=denominator != 0)

        # Aplicar máscara se fornecida
        if mask_array is not None:
            ndvi = np.where(mask_array, ndvi, np.nan)

        return ndvi

    @staticmethod
    def load_band_from_url(
        url: str, bbox: Optional[Tuple[float, float, float, float]] = None
    ) -> Tuple[np.ndarray, dict]:
        """
        Carrega uma banda espectral de uma URL.

        Args:
            url: URL do arquivo raster (GeoTIFF)
            bbox: Bounding box opcional (min_lon, min_lat, max_lon, max_lat) em EPSG:4326

        Returns:
            Tupla (array_dados, metadados)
        """
        with rasterio.open(url) as src:
            if bbox:
                from shapely.geometry import box
                from shapely.ops import transform as shapely_transform
                from pyproj import Transformer

                # Criar geometria em lat/lon (EPSG:4326)
                geom = box(*bbox)

                # Se o raster não está em EPSG:4326, reprojetar a geometria
                if src.crs and src.crs != 'EPSG:4326':
                    # Criar transformador de EPSG:4326 para CRS do raster
                    transformer = Transformer.from_crs(
                        "EPSG:4326",
                        src.crs,
                        always_xy=True
                    )

                    # Reprojetar geometria
                    geom = shapely_transform(transformer.transform, geom)

                geom_proj = [geom.__geo_interface__]

                # Recortar para a região de interesse
                out_image, out_transform = mask(src, geom_proj, crop=True)
                out_meta = src.meta.copy()
                out_meta.update({
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform
                })

                return out_image[0], out_meta
            else:
                data = src.read(1)
                return data, src.meta.copy()

    @staticmethod
    def create_cloud_mask(
        scl_band: np.ndarray, satellite: str = "sentinel-2"
    ) -> np.ndarray:
        """
        Cria máscara de nuvens a partir da banda de classificação de cena.

        Args:
            scl_band: Scene Classification Layer (Sentinel-2) ou QA_PIXEL (Landsat)
            satellite: "sentinel-2" ou "landsat-8"

        Returns:
            Array booleano (True = válido, False = nuvem/sombra)
        """
        if satellite == "sentinel-2":
            # SCL values: https://sentinels.copernicus.eu/web/sentinel/technical-guides/sentinel-2-msi/level-2a/algorithm
            # 0: No Data, 1: Saturated/Defective, 3: Cloud Shadows, 8: Cloud medium probability, 9: Cloud high probability, 10: Thin cirrus
            invalid_classes = [0, 1, 3, 8, 9, 10]
            mask = ~np.isin(scl_band, invalid_classes)
        elif satellite == "landsat-8":
            # Landsat QA_PIXEL bit interpretation
            # Bit 3: Cloud, Bit 4: Cloud Shadow
            cloud_bit = 1 << 3
            shadow_bit = 1 << 4
            mask = ~((scl_band & cloud_bit) | (scl_band & shadow_bit))
        else:
            raise ValueError(f"Satélite não suportado: {satellite}")

        return mask

    @staticmethod
    def classify_ndvi(ndvi: np.ndarray) -> np.ndarray:
        """
        Classifica valores NDVI em categorias.

        Args:
            ndvi: Array com valores NDVI

        Returns:
            Array com classes (0: water, 1: bare_soil, 2: sparse_veg, 3: moderate_veg, 4: dense_veg)
        """
        classified = np.full_like(ndvi, -1, dtype=np.int8)

        for idx, (class_name, (min_val, max_val)) in enumerate(NDVI_CLASSES.items()):
            mask = (ndvi >= min_val) & (ndvi < max_val)
            classified[mask] = idx

        return classified

    @staticmethod
    def calculate_statistics(ndvi: np.ndarray) -> dict:
        """
        Calcula estatísticas do NDVI.

        Args:
            ndvi: Array com valores NDVI

        Returns:
            Dicionário com estatísticas (mean, median, std, min, max, valid_pixels)
        """
        # Remover NaN para cálculos
        valid_ndvi = ndvi[~np.isnan(ndvi)]

        if len(valid_ndvi) == 0:
            return {
                "mean": None,
                "median": None,
                "std": None,
                "min": None,
                "max": None,
                "valid_pixels": 0,
                "total_pixels": ndvi.size,
            }

        return {
            "mean": float(np.mean(valid_ndvi)),
            "median": float(np.median(valid_ndvi)),
            "std": float(np.std(valid_ndvi)),
            "min": float(np.min(valid_ndvi)),
            "max": float(np.max(valid_ndvi)),
            "valid_pixels": len(valid_ndvi),
            "total_pixels": ndvi.size,
        }

    @staticmethod
    def calculate_class_statistics(ndvi: np.ndarray) -> dict:
        """
        Calcula estatísticas por classe de vegetação.

        Args:
            ndvi: Array com valores NDVI

        Returns:
            Dicionário com estatísticas por classe
        """
        classified = NDVICalculator.classify_ndvi(ndvi)
        valid_ndvi = ~np.isnan(ndvi)

        stats = {}
        class_names = list(NDVI_CLASSES.keys())

        for idx, class_name in enumerate(class_names):
            mask = (classified == idx) & valid_ndvi
            pixel_count = np.sum(mask)
            percentage = (pixel_count / np.sum(valid_ndvi) *
                          100) if np.sum(valid_ndvi) > 0 else 0

            stats[class_name] = {
                "pixel_count": int(pixel_count),
                "percentage": float(percentage),
                "ndvi_range": NDVI_CLASSES[class_name],
            }

        return stats

    @staticmethod
    def save_geotiff(
        ndvi: np.ndarray,
        output_path: str,
        metadata: dict,
        compress: str = "lzw",
    ) -> None:
        """
        Salva NDVI como GeoTIFF.

        Args:
            ndvi: Array com valores NDVI
            output_path: Caminho para salvar o arquivo
            metadata: Metadados do rasterio
            compress: Método de compressão ("lzw", "deflate", "none")
        """
        # Atualizar metadados
        out_meta = metadata.copy()
        out_meta.update({
            "dtype": rasterio.float32,
            "count": 1,
            "compress": compress,
            "nodata": np.nan,
        })

        # Escrever arquivo
        with rasterio.open(output_path, "w", **out_meta) as dst:
            dst.write(ndvi.astype(np.float32), 1)

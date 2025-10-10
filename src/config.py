# Configurações da aplicação NDVI Calculator

# Limites de área para evitar downloads excessivos
MAX_AREA_KM2 = 100  # km²

# Configurações de satélite
SATELLITE_CONFIG = {
    "sentinel-2": {
        "collection": "sentinel-2-l2a",
        "resolution": 10,  # metros
        "bands": {
            "red": "B04",
            "nir": "B08",
            "scl": "SCL"  # Scene Classification Layer
        }
    },
    "landsat-8": {
        "collection": "landsat-c2-l2",
        "resolution": 30,
        "bands": {
            "red": "B4",
            "nir": "B5",
            "qa": "QA_PIXEL"
        }
    }
}

# Configurações de cloud cover
DEFAULT_CLOUD_COVER_MAX = 20  # %

# Configurações de cache
CACHE_DIR = "data/cache"
CACHE_EXPIRY_DAYS = 30

# Configurações de exportação
OUTPUT_DIR = "outputs"
DEFAULT_COLOR_PALETTE = "RdYlGn"  # Red-Yellow-Green

# STAC API endpoints
STAC_ENDPOINTS = {
    "microsoft": "https://planetarycomputer.microsoft.com/api/stac/v1",
    "element84": "https://earth-search.aws.element84.com/v1"
}

# Classificação NDVI
NDVI_CLASSES = {
    "water": (-1.0, 0.0),
    "bare_soil": (0.0, 0.2),
    "sparse_vegetation": (0.2, 0.4),
    "moderate_vegetation": (0.4, 0.6),
    "dense_vegetation": (0.6, 1.0)
}

# Configurações da UI
UI_CONFIG = {
    "default_center": [-15.7801, -47.9292],  # Brasília
    "default_zoom": 10,
    "map_height": 600,
    "max_file_size_mb": 50
}

# Instruções do GitHub Copilot - Calculadora NDVI

## Contexto do Projeto
Aplicação para cálculo de NDVI (Normalized Difference Vegetation Index) usando dados de satélite abertos e gratuitos.

## Tecnologias Principais
- **Python 3.11+**
- **Gerenciador de pacotes**: uv
- **Interface**: Gradio (opcionalmente Streamlit)
- **Dados**: Sentinel-2 via Google Earth Engine ou STAC API (sem APIs pagas)
- **Processamento**: rasterio, numpy, xarray
- **Mapas**: folium, leafmap, ipyleaflet

## Fontes de Dados Abertas
1. **Sentinel-2** (ESA): Imagens multiespectrais gratuitas, 10m de resolução
2. **Landsat 8/9** (NASA/USGS): Dados históricos e atuais
3. **STAC Catalogs**: Microsoft Planetary Computer, Element84 Earth Search
4. **Copernicus Data Space Ecosystem**: API gratuita com limite generoso

## Arquitetura da Aplicação

### Módulos Principais
```
nvdi_calc/
├── src/
│   ├── data/
│   │   ├── satellite_fetcher.py    # Busca dados de satélite
│   │   ├── stac_client.py          # Cliente STAC API
│   │   └── preprocessor.py         # Pré-processamento de imagens
│   ├── processing/
│   │   ├── ndvi_calculator.py      # Cálculo do NDVI
│   │   ├── statistics.py           # Estatísticas e métricas
│   │   └── time_series.py          # Análise temporal
│   ├── visualization/
│   │   ├── map_viewer.py           # Visualização de mapas
│   │   ├── charts.py               # Gráficos e plots
│   │   └── export.py               # Exportação de resultados
│   └── ui/
│       ├── gradio_app.py           # Interface Gradio
│       └── components.py           # Componentes reutilizáveis
├── tests/
├── data/                           # Cache local de dados
└── outputs/                        # Resultados exportados
```

## Parâmetros de Entrada Necessários

### 1. Seleção Espacial
- **Região de interesse (ROI)**: Desenho de polígono no mapa ou upload de GeoJSON/Shapefile
- **Coordenadas**: Latitude/Longitude ou caixa delimitadora (bbox)
- **Área máxima**: Limitar para evitar downloads excessivos

### 2. Parâmetros Temporais
- **Data inicial e final**: Período de análise
- **Frequência**: Mensal, sazonal, anual
- **Composição temporal**: Mediana, média, máximo NDVI

### 3. Parâmetros de Qualidade
- **Cobertura de nuvens**: Threshold máximo (ex: 20%)
- **Máscara de nuvens**: Aplicar ou não
- **Filtros atmosféricos**: Correção atmosférica

### 4. Parâmetros de Processamento
- **Resolução espacial**: 10m, 20m, 30m
- **Satélite/Sensor**: Sentinel-2, Landsat 8/9
- **Bandas espectrais**: NIR (B8) e Red (B4) para Sentinel-2

### 5. Parâmetros de Saída
- **Formato de exportação**: GeoTIFF, PNG, CSV (estatísticas)
- **Paleta de cores**: Viridis, RdYlGn, personalizada
- **Estatísticas**: Média, mediana, desvio padrão por classe NDVI
- **Visualizações**: Mapa de calor, série temporal, histograma

## Funcionalidades Profissionais

### Essenciais
- ✅ Seleção interativa de ROI no mapa
- ✅ Download automático de imagens Sentinel-2/Landsat
- ✅ Cálculo NDVI com máscara de nuvens
- ✅ Visualização de mapa com escala de cores
- ✅ Exportação de resultados (GeoTIFF, PNG)

### Avançadas
- ✅ Análise de série temporal (gráficos de tendência)
- ✅ Comparação multi-temporal (antes/depois)
- ✅ Estatísticas zonais (por classe de uso do solo)
- ✅ Detecção de mudanças de vegetação
- ✅ Classificação de vegetação (saudável/estressada/solo exposto)
- ✅ Cache inteligente de imagens baixadas
- ✅ Processamento paralelo para grandes áreas
- ✅ Relatórios em PDF com mapas e gráficos

## Boas Práticas de Código

### Estilo
- Seguir PEP 8 e type hints
- Docstrings no formato Google ou NumPy
- Testes unitários com pytest
- Validação de entrada com pydantic

### Performance
- Usar lazy loading para grandes rasters
- Cache com functools.lru_cache ou joblib
- Processamento chunked com dask quando necessário
- Validar limites de área/tempo antes de processar

### Segurança
- Validar inputs do usuário (coordenadas, datas)
- Limitar tamanho de downloads
- Timeout em requests HTTP
- Sanitizar nomes de arquivos

### UX
- Feedback de progresso (progress bars)
- Mensagens de erro claras e acionáveis
- Preview de resultados antes de processar
- Tutoriais interativos ou exemplos

## Dependências Principais
```toml
dependencies = [
    "gradio>=4.0",
    "numpy>=1.24",
    "rasterio>=1.3",
    "geopandas>=0.14",
    "folium>=0.15",
    "leafmap>=0.30",
    "pystac-client>=0.7",
    "planetary-computer>=1.0",
    "xarray>=2023.1",
    "matplotlib>=3.7",
    "plotly>=5.17",
    "pillow>=10.0",
    "shapely>=2.0",
    "pyproj>=3.6",
    "requests>=2.31",
    "tqdm>=4.66",
]
```

## Fórmulas e Algoritmos

### NDVI
```
NDVI = (NIR - Red) / (NIR + Red)
```
- Valores: -1 a +1
- < 0: Água, nuvens
- 0 - 0.2: Solo exposto, rochas
- 0.2 - 0.4: Vegetação esparsa
- 0.4 - 0.6: Vegetação moderada
- > 0.6: Vegetação densa/saudável

### Bandas Sentinel-2
- Red: B4 (665nm)
- NIR: B8 (842nm)
- Resolução: 10m

### Bandas Landsat 8/9
- Red: B4 (640nm)
- NIR: B5 (865nm)
- Resolução: 30m

## Exemplos de Uso

### API STAC (Microsoft Planetary Computer)
```python
from pystac_client import Client
import planetary_computer as pc

catalog = Client.open(
    "https://planetarycomputer.microsoft.com/api/stac/v1"
)

search = catalog.search(
    collections=["sentinel-2-l2a"],
    bbox=bbox,
    datetime="2024-01-01/2024-12-31",
    query={"eo:cloud_cover": {"lt": 20}}
)

items = list(search.items())
```

## Considerações de Implementação
1. **Começar simples**: MVP com região fixa e data única
2. **Iterar**: Adicionar parâmetros progressivamente
3. **Testar**: Usar regiões pequenas durante desenvolvimento
4. **Documentar**: README com exemplos e screenshots
5. **Deploy**: Considerar Hugging Face Spaces (gratuito) para Gradio

## Links Úteis
- [Sentinel-2 Bands](https://gisgeography.com/sentinel-2-bands-combinations/)
- [STAC Specification](https://stacspec.org/)
- [Microsoft Planetary Computer](https://planetarycomputer.microsoft.com/)
- [Awesome NDVI](https://github.com/topics/ndvi)

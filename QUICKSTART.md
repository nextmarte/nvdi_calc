# 🚀 Guia de Início Rápido

## Instalação e Configuração

```bash
# Clone o repositório
git clone <seu-repo>
cd nvdi_calc

# Sincronize as dependências
uv sync

# Ative o ambiente virtual
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate      # Windows
```

## Executar a Aplicação Web

```bash
# Método 1: Com uv
uv run python main.py

# Método 2: No ambiente virtual
python main.py
```

A aplicação abrirá automaticamente no navegador em `http://localhost:7860`

## Exemplo de Uso via API

```python
from src.data.stac_client import STACClient
from src.processing.ndvi_calculator import NDVICalculator

# 1. Configurar busca
client = STACClient()
bbox = (-47.95, -15.85, -47.85, -15.75)  # Brasília
date_range = ("2024-01-01", "2024-12-31")

# 2. Buscar melhor imagem
item = client.get_best_image(
    bbox=bbox,
    date_range=date_range,
    satellite="sentinel-2",
    max_cloud_cover=20
)

# 3. Carregar bandas
band_urls = client.get_band_urls(item, satellite="sentinel-2")
red_band, red_meta = NDVICalculator.load_band_from_url(band_urls["red"], bbox)
nir_band, _ = NDVICalculator.load_band_from_url(band_urls["nir"], bbox)

# 4. Calcular NDVI
ndvi = NDVICalculator.calculate_ndvi(nir_band, red_band)

# 5. Obter estatísticas
stats = NDVICalculator.calculate_statistics(ndvi)
print(f"NDVI médio: {stats['mean']:.4f}")

# 6. Salvar resultado
NDVICalculator.save_geotiff(ndvi, "output.tif", red_meta)
```

## Executar Exemplo Completo

```bash
uv run python examples/example_usage.py
```

Este exemplo demonstra:
- Busca de imagens
- Cálculo de NDVI
- Criação de visualizações
- Exportação de resultados

## Executar Testes

```bash
# Todos os testes
uv run pytest

# Com cobertura
uv run pytest --cov=src --cov-report=html

# Teste específico
uv run pytest tests/test_ndvi_calculator.py
```

## Estrutura de Coordenadas

Para definir sua região de interesse, você precisa de 4 coordenadas:

```
bbox = (min_longitude, min_latitude, max_longitude, max_latitude)

Exemplo (Brasília):
bbox = (-47.95, -15.85, -47.85, -15.75)
```

**Dicas para encontrar coordenadas:**
- Use Google Maps: clique com botão direito > coordenadas
- Use [bboxfinder.com](http://bboxfinder.com) para desenhar
- Use [geojson.io](http://geojson.io) para polígonos complexos

## Limitações

- **Área máxima:** 100 km² por processamento
- **Resolução:**
  - Sentinel-2: 10 metros
  - Landsat 8/9: 30 metros
- **Dados disponíveis:**
  - Sentinel-2: desde 2015
  - Landsat 8: desde 2013
  - Landsat 9: desde 2021

## Interpretação dos Resultados

| NDVI | Cor | Significado |
|------|-----|-------------|
| < 0 | 🔴 Vermelho | Água, nuvens, neve |
| 0 - 0.2 | 🟠 Laranja | Solo exposto, áreas urbanas |
| 0.2 - 0.4 | 🟡 Amarelo | Vegetação esparsa, pastagem seca |
| 0.4 - 0.6 | 🟢 Verde claro | Vegetação moderada, culturas |
| > 0.6 | 🟢 Verde escuro | Vegetação densa, floresta |

## Troubleshooting

### Erro: "Nenhuma imagem encontrada"
- Verifique se a região está correta
- Aumente o período de busca
- Aumente a tolerância de nuvens
- Tente outro satélite

### Erro: "Área muito grande"
- Reduza o tamanho do bbox
- Processe em partes menores
- Use resolução menor (Landsat)

### Erro de conexão
- Verifique sua internet
- O Microsoft Planetary Computer pode estar indisponível
- Tente novamente em alguns minutos

## Suporte

Para problemas ou dúvidas:
1. Verifique a documentação completa no README.md
2. Consulte os exemplos em `examples/`
3. Abra uma issue no GitHub

## Próximos Passos

Depois de usar o básico, explore:
- 📊 Análise de séries temporais
- 🔄 Comparação multi-temporal
- 📈 Detecção de mudanças
- 📄 Geração de relatórios em PDF

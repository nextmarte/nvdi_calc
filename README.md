# 🌱 Calculadora NDVI

Aplicação profissional para cálculo de NDVI (Normalized Difference Vegetation Index) usando dados de satélite abertos e gratuitos.

## 🎯 Características

- 🛰️ **Dados Abertos**: Sentinel-2 (10m) e Landsat 8/9 (30m) via STAC API
- 🗺️ **Seleção Interativa**: Desenhe a região de interesse no mapa
- 📊 **Análise Temporal**: Séries temporais e detecção de mudanças
- 🎨 **Visualizações**: Mapas de calor, gráficos e estatísticas
- 💾 **Exportação**: GeoTIFF, PNG, CSV e relatórios em PDF
- ⚡ **Performance**: Cache inteligente e processamento otimizado

## 🚀 Instalação

### Requisitos
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (gerenciador de pacotes)

### Setup

```bash
# Clone o repositório
git clone <seu-repo>
cd nvdi_calc

# Instale as dependências com uv
uv sync

# Ative o ambiente virtual
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows
```

## 📖 Uso

```bash
# Execute a aplicação
uv run python main.py
```

A interface Gradio será aberta no navegador. Então:

1. **Selecione a região** de interesse no mapa
2. **Configure os parâmetros**:
   - Período (data inicial e final)
   - Satélite (Sentinel-2 ou Landsat)
   - Cobertura máxima de nuvens
   - Paleta de cores
3. **Calcule o NDVI** e visualize os resultados
4. **Exporte** os dados processados

## 🗂️ Estrutura do Projeto

```
nvdi_calc/
├── src/
│   ├── data/              # Busca e pré-processamento de dados
│   ├── processing/        # Cálculo NDVI e análises
│   ├── visualization/     # Mapas e gráficos
│   └── ui/                # Interface Gradio
├── tests/                 # Testes unitários
├── data/                  # Cache de dados baixados
├── outputs/               # Resultados exportados
└── main.py                # Ponto de entrada da aplicação
```

## 🌍 Fontes de Dados

- **Sentinel-2**: ESA Copernicus (resolução 10m)
- **Landsat 8/9**: NASA/USGS (resolução 30m)
- **STAC Catalogs**: Microsoft Planetary Computer, Element84

## 📈 Interpretação do NDVI

| Valor NDVI | Interpretação |
|------------|---------------|
| < 0 | Água, nuvens, neve |
| 0 - 0.2 | Solo exposto, rochas |
| 0.2 - 0.4 | Vegetação esparsa |
| 0.4 - 0.6 | Vegetação moderada |
| > 0.6 | Vegetação densa/saudável |

## 🧪 Desenvolvimento

```bash
# Execute os testes
uv run pytest

# Formatação de código
uv run black src/
uv run isort src/

# Type checking
uv run mypy src/
```

## 📝 Licença

MIT License

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor, abra uma issue ou PR.

## 📚 Referências

- [Sentinel-2 Bands](https://gisgeography.com/sentinel-2-bands-combinations/)
- [STAC Specification](https://stacspec.org/)
- [Microsoft Planetary Computer](https://planetarycomputer.microsoft.com/)

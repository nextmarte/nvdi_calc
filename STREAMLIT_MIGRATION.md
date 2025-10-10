# 🔄 Migração para Streamlit

## Data: 10/10/2025

### Por que mudamos do Gradio para Streamlit?

O Gradio apresentou problemas com a captura automática de coordenadas do mapa. A integração JavaScript necessária para passar dados do Folium para os campos do Gradio era complexa e não funcionou de forma confiável.

### Vantagens do Streamlit

✅ **Integração nativa com Folium** via `streamlit-folium`
✅ **Captura automática de desenhos** através do retorno `all_drawings`
✅ **Session state integrado** para gerenciar coordenadas
✅ **Melhor experiência de desenvolvimento** com hot reload
✅ **Layout mais flexível** com colunas e sidebar
✅ **Componentes interativos nativos** sem necessidade de JavaScript customizado

## Mudanças Implementadas

### 1. Dependências Adicionadas
```bash
uv add streamlit streamlit-folium pydeck
```

Pacotes instalados:
- `streamlit==1.50.0` - Framework web
- `streamlit-folium==0.25.3` - Integração com Folium
- `pydeck==0.9.1` - Mapas 3D (opcional)

### 2. Nova Interface: `src/ui/streamlit_app.py`

**Características principais:**

#### Mapa Interativo
```python
from streamlit_folium import st_folium
import folium
from folium.plugins import Draw

# Mapa com ferramentas de desenho
m = folium.Map(location=(-15.8, -47.9), zoom_start=10)
draw = Draw(draw_options={'polygon': {...}, 'rectangle': {...}})
draw.add_to(m)

# Captura automática de desenhos
map_data = st_folium(m, returned_objects=["all_drawings"])
```

#### Captura de Coordenadas
```python
def extract_bbox_from_draw(self, draw_data: dict):
    """Extrai bbox dos desenhos automaticamente."""
    if draw_data and draw_data.get('all_drawings'):
        drawings = draw_data['all_drawings']
        last_drawing = drawings[-1]
        geometry = last_drawing['geometry']
        coords = geometry['coordinates'][0]
        
        lons = [p[0] for p in coords]
        lats = [p[1] for p in coords]
        
        return (min(lons), min(lats), max(lons), max(lats))
    return None
```

#### Session State para Coordenadas
```python
# Inicializar
if 'bbox' not in st.session_state:
    st.session_state.bbox = None

# Atualizar quando desenhar
bbox = self.extract_bbox_from_draw(map_data)
if bbox and bbox != st.session_state.bbox:
    st.session_state.bbox = bbox
    st.rerun()  # Recarrega a interface com novos valores
```

#### Sidebar com Parâmetros
```python
def render_sidebar(self):
    st.sidebar.title("🌱 Calculadora NDVI")
    
    # Coordenadas (atualizadas automaticamente)
    if st.session_state.bbox:
        min_lon, min_lat, max_lon, max_lat = st.session_state.bbox
        st.sidebar.success("✅ Área selecionada no mapa!")
    
    # Campos editáveis
    min_lon_input = st.sidebar.number_input("Lon Mín", value=min_lon)
    # ... outros campos
    
    # Botão de processar
    if st.sidebar.button("🚀 Calcular NDVI"):
        self.process_ndvi(...)
```

#### Visualização de Resultados
```python
# Tabs para organizar resultados
tab1, tab2, tab3 = st.tabs(["🗺️ Mapa", "📊 Histograma", "📈 Estatísticas"])

with tab1:
    st.pyplot(results['map'])

with tab2:
    st.pyplot(results['histogram'])

with tab3:
    stats_df = pd.DataFrame(...)
    st.dataframe(stats_df, use_container_width=True)
```

### 3. Atualização do `main.py`

```python
import subprocess
import sys
from pathlib import Path

def main():
    app_path = Path(__file__).parent / "src" / "ui" / "streamlit_app.py"
    
    subprocess.run([
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_path),
        "--server.port=8501",
        "--server.address=0.0.0.0",
        "--theme.primaryColor=#00cc66"
    ])
```

### 4. Correção de Importações

**Problema:** Streamlit executa o arquivo diretamente, não como módulo, então importações relativas (`from ..data`) não funcionam.

**Solução:** Adicionar o diretório raiz ao `sys.path` antes das importações:

```python
import sys
from pathlib import Path

# Adicionar diretório raiz ao path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# Agora usar importações absolutas
from src.data.stac_client import STACClient
from src.processing.ndvi_calculator import NDVICalculator
# ...
```

⚠️ **IMPORTANTE:** As importações de `src.*` devem vir **DEPOIS** de configurar o `sys.path`!

## Como Usar

### Executar a Aplicação
```bash
# Com uv (recomendado)
uv run python main.py

# Ou diretamente
uv run streamlit run src/ui/streamlit_app.py
```

### Acessar
Abra o navegador em: **http://localhost:8501**

### Fluxo de Trabalho

1. **Desenhe** uma área no mapa usando as ferramentas no canto superior esquerdo
   - 📐 Retângulo
   - ✏️ Polígono
   
2. **Observe** as coordenadas sendo atualizadas automaticamente na sidebar

3. **Configure** os parâmetros:
   - Período (datas)
   - Satélite (Sentinel-2 ou Landsat-8)
   - Cobertura máxima de nuvens
   - Paleta de cores

4. **Clique** em "🚀 Calcular NDVI"

5. **Visualize** os resultados nas 3 tabs:
   - Mapa de calor do NDVI
   - Histograma de distribuição
   - Estatísticas detalhadas

## Diferenças vs Gradio

| Aspecto | Gradio | Streamlit |
|---------|--------|-----------|
| **Captura de Coordenadas** | ❌ Requer JavaScript customizado | ✅ Nativo via `st_folium` |
| **Atualização de Campos** | ❌ Complexo com `elem_id` | ✅ Automático via `session_state` |
| **Layout** | Blocos e abas | Sidebar, colunas, expanders |
| **Reload** | Não automático | ✅ Hot reload durante desenvolvimento |
| **Componentes de Mapa** | HTML embed | ✅ Integração bidirecional |
| **Porta Padrão** | 7860 | 8501 |
| **Complexidade** | Média | Baixa |

## Módulos Reutilizados

Todos os módulos de backend foram mantidos sem alterações:

✅ `src/data/stac_client.py` - Busca de imagens
✅ `src/processing/ndvi_calculator.py` - Cálculo NDVI
✅ `src/visualization/map_viewer.py` - Visualização de mapas
✅ `src/visualization/charts.py` - Gráficos

Apenas a interface foi reescrita de Gradio → Streamlit.

## Problemas Resolvidos

### ✅ Captura Automática de Coordenadas
- **Antes:** JavaScript injetado no Folium tentando atualizar campos Gradio por label
- **Depois:** `st_folium` retorna `all_drawings` diretamente no Python

### ✅ Importações
- **Antes:** Importações relativas (`from ..data`)
- **Depois:** `sys.path` configurado + importações absolutas (`from src.data`)

### ✅ Responsividade
- **Antes:** Campos não atualizavam visualmente
- **Depois:** `st.rerun()` força atualização da interface

## Próximos Passos

- [ ] Adicionar cache com `@st.cache_data` para imagens baixadas
- [ ] Implementar análise de série temporal
- [ ] Exportar resultados (GeoTIFF, PNG, CSV)
- [ ] Comparação multi-temporal (antes/depois)
- [ ] Deploy em Streamlit Cloud (gratuito)

## Comandos Úteis

```bash
# Verificar instalação
uv run streamlit --version

# Limpar cache do Streamlit
uv run streamlit cache clear

# Abrir configurações
uv run streamlit config show

# Ver documentação
uv run streamlit docs
```

## Referências

- [Streamlit Documentation](https://docs.streamlit.io/)
- [streamlit-folium](https://github.com/randyzwitch/streamlit-folium)
- [Folium Draw Plugin](https://python-visualization.github.io/folium/plugins.html#folium.plugins.Draw)

---

**Status:** ✅ Migração completa e funcional!
**Data:** 10 de outubro de 2025
**Versão:** Streamlit 1.50.0

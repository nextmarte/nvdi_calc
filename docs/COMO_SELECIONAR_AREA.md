# 🗺️ Como Selecionar a Região no Mapa

## Métodos de Seleção

### Método 1: Mapa Interativo (Recomendado) 🎯

A interface agora tem um **mapa interativo** no topo onde você pode visualizar e selecionar sua região de interesse:

1. **Visualize o mapa** - Centralizado em Brasília por padrão
2. **Use as ferramentas de desenho** no canto superior esquerdo:
   - 📐 **Retângulo** - Para áreas regulares
   - ✏️ **Polígono** - Para áreas irregulares
3. **Desenhe sua área** de interesse diretamente no mapa
4. **Copie as coordenadas** que aparecem e cole nos campos de entrada

**Ferramentas disponíveis no mapa:**
- 🔍 Zoom in/out
- 📏 Medição de distância
- 🖊️ Editar formas desenhadas
- 🗑️ Deletar formas
- 📱 Tela cheia

### Método 2: Coordenadas Manuais 📝

Se preferir, você pode inserir as coordenadas diretamente nos campos:

**Formato do Bounding Box:**
```
min_longitude, min_latitude, max_longitude, max_latitude
```

**Exemplos de regiões prontas:**

#### 🌳 Brasília (Parque Nacional)
```
Longitude Mínima: -47.95
Latitude Mínima: -15.85
Longitude Máxima: -47.85
Latitude Máxima: -15.75
```

#### 🌴 Amazônia (Próximo a Manaus)
```
Longitude Mínima: -60.1
Latitude Mínima: -3.2
Longitude Máxima: -59.9
Latitude Máxima: -3.0
```

#### 🌾 Centro-Oeste (Área Agrícola)
```
Longitude Mínima: -54.8
Latitude Mínima: -15.7
Longitude Máxima: -54.6
Latitude Máxima: -15.5
```

#### 🏝️ Pantanal
```
Longitude Mínima: -57.5
Latitude Mínima: -19.5
Longitude Máxima: -57.3
Latitude Máxima: -19.3
```

### Método 3: Ferramentas Externas 🌐

Para áreas mais complexas ou para visualizar melhor:

1. **[BBoxFinder.com](http://bboxfinder.com)**
   - Desenhe no mapa
   - Copie as coordenadas no formato: `[min_lon, min_lat, max_lon, max_lat]`
   - Cole nos campos da aplicação

2. **[GeoJSON.io](http://geojson.io)**
   - Desenhe polígonos complexos
   - Exporte as coordenadas
   - Use o bounding box gerado

3. **Google Maps**
   - Clique com botão direito em qualquer ponto
   - Copie as coordenadas (latitude, longitude)
   - Use para definir os cantos do seu retângulo

## Como Encontrar Coordenadas

### Google Maps
1. Abra [Google Maps](https://maps.google.com)
2. Clique com botão direito no local desejado
3. Clique em "Copiar coordenadas"
4. Formato: `-15.7801, -47.9292` (latitude, longitude)

### Google Earth
1. Abra Google Earth
2. Posicione o cursor sobre o local
3. Veja as coordenadas na parte inferior

## Entendendo as Coordenadas

### Longitude (Leste-Oeste)
- **Valores negativos**: Oeste (América do Sul)
- **Valores positivos**: Leste (África, Ásia)
- **Brasil**: Entre -35° e -73°

### Latitude (Norte-Sul)
- **Valores negativos**: Sul
- **Valores positivos**: Norte
- **Brasil**: Entre +5° (norte) e -33° (sul)

### Exemplo Visual
```
        max_lat (norte)
             ↑
             |
min_lon ←----+----→ max_lon
   (oeste)   |   (leste)
             ↓
        min_lat (sul)
```

## Limitações Importantes

⚠️ **Área Máxima:** 100 km²
- Áreas maiores serão rejeitadas
- Use tiles menores para grandes regiões

⚠️ **Resolução:**
- Sentinel-2: ~10 metros/pixel
- Landsat 8: ~30 metros/pixel

💡 **Dica:** Comece com áreas pequenas (10-20 km²) para testar!

## Validação Automática

A aplicação valida automaticamente:
- ✅ Coordenadas dentro dos limites (-180 a 180° lon, -90 a 90° lat)
- ✅ Min < Max (longitude e latitude)
- ✅ Área total não excede 100 km²
- ✅ Dados disponíveis para o período selecionado

## Erros Comuns

### ❌ "Longitude mínima deve ser menor que longitude máxima"
**Solução:** Inverta os valores de longitude

### ❌ "Área muito grande"
**Solução:** Reduza o tamanho do retângulo

### ❌ "Nenhuma imagem encontrada"
**Solução:** 
- Aumente o período de busca
- Relaxe o filtro de nuvens
- Verifique se a região está correta

## Exemplo Completo

```python
# Região: Brasília - Parque Nacional
min_lon = -47.95  # Oeste
min_lat = -15.85  # Sul
max_lon = -47.85  # Leste
max_lat = -15.75  # Norte

# Período
start_date = "2024-01-01"
end_date = "2024-12-31"

# Satélite
satellite = "sentinel-2"  # 10m de resolução

# Processamento
max_cloud_cover = 20  # Máximo 20% de nuvens
```

## Dicas Profissionais

1. 🎯 **Centralize sua área** - Deixe margem nas bordas
2. 📏 **Use medição** - Ferramentas do mapa mostram área
3. 🌤️ **Ajuste nuvens** - 20-30% é um bom balanço
4. 📅 **Período amplo** - Mais chances de encontrar imagens
5. 💾 **Salve coordenadas** - Para análises futuras

## Recursos Úteis

- 🗺️ [OpenStreetMap](https://www.openstreetmap.org)
- 📍 [BBoxFinder](http://bboxfinder.com)
- ✏️ [GeoJSON.io](http://geojson.io)
- 🌍 [Google Earth Web](https://earth.google.com/web/)
- 📊 [Sentinel Hub EO Browser](https://apps.sentinel-hub.com/eo-browser/)

---

**Precisa de ajuda?** Abra uma issue no GitHub ou consulte a documentação completa!

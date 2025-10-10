"""
Componente de mapa interativo para seleção de ROI.
"""

import json
import folium
from folium import plugins
from typing import Tuple, Optional


class InteractiveMap:
    """Componente de mapa interativo para seleção de região."""

    @staticmethod
    def create_selection_map(
        center: Tuple[float, float] = (-15.7801, -47.9292),
        zoom: int = 10,
    ) -> str:
        """
        Cria um mapa interativo para seleção de ROI com captura de coordenadas.

        Args:
            center: (latitude, longitude) do centro
            zoom: Nível de zoom

        Returns:
            HTML do mapa como string com JavaScript para captura de coordenadas
        """
        # Criar mapa base
        m = folium.Map(
            location=center,
            zoom_start=zoom,
            tiles="OpenStreetMap",
            height=600,
        )

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
            edit_options={"edit": True},
        )
        draw.add_to(m)

        # Adicionar ferramentas úteis
        plugins.MeasureControl(
            position="topleft", primary_length_unit="kilometers").add_to(m)
        plugins.Fullscreen().add_to(m)

        # Adicionar instruções
        instructions_html = """
        <div style="position: fixed; top: 10px; right: 10px; width: 300px; 
                    background-color: white; border: 2px solid #333; z-index: 9999; 
                    padding: 15px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.3);">
            <h4 style="margin-top: 0; color: #2c5f2d;">🗺️ Como Usar o Mapa</h4>
            <ol style="font-size: 13px; padding-left: 20px; margin: 10px 0;">
                <li>Use os botões à esquerda para desenhar</li>
                <li>Desenhe um <b>retângulo</b> ou <b>polígono</b></li>
                <li>As coordenadas serão <b>atualizadas automaticamente</b> abaixo!</li>
            </ol>
            <p style="font-size: 12px; color: #666; margin: 5px 0;">
                💡 <b>Dica:</b> Áreas menores = processamento mais rápido!
            </p>
            <div id="coord-display" style="margin-top: 10px; padding: 10px; background: #f0f0f0; border-radius: 3px; font-size: 11px; display: none;">
                <b>Coordenadas selecionadas:</b><br>
                <span id="bbox-text">Desenhe uma área</span>
            </div>
        </div>
        """
        m.get_root().html.add_child(folium.Element(instructions_html))

        # JavaScript para capturar coordenadas do desenho e atualizar campos Gradio
        capture_script = """
        <script>
        // Função para extrair bbox de uma layer
        function getBboxFromLayer(layer) {
            let latlngs = [];
            
            if (layer instanceof L.Rectangle) {
                latlngs = layer.getLatLngs()[0];
            } else if (layer instanceof L.Polygon) {
                latlngs = layer.getLatLngs()[0];
            } else if (layer.toGeoJSON) {
                let geojson = layer.toGeoJSON();
                if (geojson.geometry.coordinates) {
                    let coords = geojson.geometry.coordinates[0];
                    latlngs = coords.map(c => ({lat: c[1], lng: c[0]}));
                }
            }
            
            if (latlngs.length === 0) return null;
            
            let lats = latlngs.map(ll => ll.lat);
            let lngs = latlngs.map(ll => ll.lng);
            
            return {
                min_lon: Math.min(...lngs).toFixed(4),
                min_lat: Math.min(...lats).toFixed(4),
                max_lon: Math.max(...lngs).toFixed(4),
                max_lat: Math.max(...lats).toFixed(4)
            };
        }
        
        // Função para atualizar os campos Gradio
        function updateGradioFields(bbox) {
            if (!bbox) return;
            
            console.log('Atualizando coordenadas:', bbox);
            
            // Atualizar display no mapa
            let display = document.getElementById('coord-display');
            let text = document.getElementById('bbox-text');
            if (display && text) {
                display.style.display = 'block';
                text.innerHTML = `
                    Lon: ${bbox.min_lon} a ${bbox.max_lon}<br>
                    Lat: ${bbox.min_lat} a ${bbox.max_lat}
                `;
            }
            
            // Tentar atualizar campos Gradio com múltiplas estratégias
            setTimeout(() => {
                try {
                    let updated = 0;
                    
                    // Estratégia 1: Buscar por elem_id
                    const updateByElemId = (elemId, value) => {
                        // Tentar direto
                        let el = document.getElementById(elemId);
                        if (el && el.tagName === 'INPUT') {
                            el.value = value;
                            el.dispatchEvent(new Event('input', { bubbles: true }));
                            el.dispatchEvent(new Event('change', { bubbles: true }));
                            return true;
                        }
                        
                        // Tentar encontrar dentro de container com esse ID
                        let container = document.getElementById(elemId);
                        if (container) {
                            let input = container.querySelector('input[type="number"]');
                            if (input) {
                                input.value = value;
                                input.dispatchEvent(new Event('input', { bubbles: true }));
                                input.dispatchEvent(new Event('change', { bubbles: true }));
                                return true;
                            }
                        }
                        
                        // Tentar encontrar input que tenha elem_id como parte do ID
                        let inputs = document.querySelectorAll('input[type="number"]');
                        for (let input of inputs) {
                            if (input.id.includes(elemId)) {
                                input.value = value;
                                input.dispatchEvent(new Event('input', { bubbles: true }));
                                input.dispatchEvent(new Event('change', { bubbles: true }));
                                return true;
                            }
                        }
                        return false;
                    };
                    
                    if (updateByElemId('min_lon_input', bbox.min_lon)) updated++;
                    if (updateByElemId('min_lat_input', bbox.min_lat)) updated++;
                    if (updateByElemId('max_lon_input', bbox.max_lon)) updated++;
                    if (updateByElemId('max_lat_input', bbox.max_lat)) updated++;
                    
                    // Estratégia 2: Se não funcionou, buscar por label
                    if (updated === 0) {
                        let inputs = document.querySelectorAll('input[type="number"]');
                        
                        inputs.forEach(input => {
                            // Buscar label em diferentes posições
                            let container = input.closest('.wrap');
                            if (!container) container = input.closest('.gr-box');
                            if (!container) container = input.parentElement;
                            
                            let label = container ? container.querySelector('label') : null;
                            if (!label) return;
                            
                            let labelText = label.textContent.toLowerCase();
                            
                            if (labelText.includes('longitude') && labelText.includes('mínima')) {
                                input.value = bbox.min_lon;
                                input.dispatchEvent(new Event('input', { bubbles: true }));
                                input.dispatchEvent(new Event('change', { bubbles: true }));
                                updated++;
                            } else if (labelText.includes('latitude') && labelText.includes('mínima')) {
                                input.value = bbox.min_lat;
                                input.dispatchEvent(new Event('input', { bubbles: true }));
                                input.dispatchEvent(new Event('change', { bubbles: true }));
                                updated++;
                            } else if (labelText.includes('longitude') && labelText.includes('máxima')) {
                                input.value = bbox.max_lon;
                                input.dispatchEvent(new Event('input', { bubbles: true }));
                                input.dispatchEvent(new Event('change', { bubbles: true }));
                                updated++;
                            } else if (labelText.includes('latitude') && labelText.includes('máxima')) {
                                input.value = bbox.max_lat;
                                input.dispatchEvent(new Event('input', { bubbles: true }));
                                input.dispatchEvent(new Event('change', { bubbles: true }));
                                updated++;
                            }
                        });
                    }
                    
                    if (updated > 0) {
                        console.log(`✅ ${updated} campos atualizados com sucesso!`);
                    } else {
                        console.warn('⚠️ Nenhum campo foi atualizado. Estrutura do DOM:');
                        console.log(document.querySelectorAll('input[type="number"]'));
                    }
                } catch (e) {
                    console.error('❌ Erro ao atualizar campos:', e);
                }
            }, 500);
        }
        
        // Tornar função global para debug
        window.updateGradioFieldsManual = function(minLon, minLat, maxLon, maxLat) {
            updateGradioFields({
                min_lon: minLon.toFixed(4),
                min_lat: minLat.toFixed(4),
                max_lon: maxLon.toFixed(4),
                max_lat: maxLat.toFixed(4)
            });
        };
        
        // Aguardar mapa carregar
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🗺️ Inicializando captura de coordenadas...');
            setTimeout(() => {
                // Encontrar o mapa Leaflet
                let maps = document.querySelectorAll('.folium-map');
                if (maps.length === 0) {
                    console.warn('⚠️ Nenhum mapa Folium encontrado');
                    return;
                }
                
                console.log(`✅ ${maps.length} mapa(s) encontrado(s)`);
                
                // Pegar a primeira instância do mapa
                let mapId = maps[0].id;
                if (window[mapId]) {
                    let map = window[mapId];
                    console.log('✅ Instância do mapa obtida:', mapId);
                    
                    // Listener para quando desenhar algo
                    map.on('draw:created', function(e) {
                        console.log('🎨 Forma desenhada:', e.layerType);
                        let bbox = getBboxFromLayer(e.layer);
                        if (bbox) {
                            console.log('📍 BBox extraído:', bbox);
                            updateGradioFields(bbox);
                        }
                    });
                    
                    // Listener para quando editar
                    map.on('draw:edited', function(e) {
                        console.log('✏️ Formas editadas');
                        e.layers.eachLayer(function(layer) {
                            let bbox = getBboxFromLayer(layer);
                            if (bbox) {
                                console.log('📍 BBox extraído:', bbox);
                                updateGradioFields(bbox);
                            }
                        });
                    });
                    
                    console.log('🎯 Captura de coordenadas ativada! Use o console para debug:');
                    console.log('   - window.updateGradioFieldsManual(-47.95, -15.85, -47.85, -15.75)');
                } else {
                    console.error('❌ Não foi possível obter instância do mapa');
                }
            }, 1500);
        });
        </script>
        """

        m.get_root().html.add_child(folium.Element(capture_script))

        return m._repr_html_()

    @staticmethod
    def extract_bbox_from_geojson(geojson_str: str) -> Optional[Tuple[float, float, float, float]]:
        """
        Extrai bounding box de um GeoJSON.

        Args:
            geojson_str: String JSON com geometria desenhada

        Returns:
            Tupla (min_lon, min_lat, max_lon, max_lat) ou None
        """
        if not geojson_str or geojson_str == "":
            return None

        try:
            geojson = json.loads(geojson_str)

            # Se é uma FeatureCollection
            if geojson.get("type") == "FeatureCollection":
                features = geojson.get("features", [])
                if not features:
                    return None
                # Pegar primeira feature
                geometry = features[0].get("geometry", {})
            # Se é uma Feature
            elif geojson.get("type") == "Feature":
                geometry = geojson.get("geometry", {})
            # Se já é uma geometria
            else:
                geometry = geojson

            coordinates = geometry.get("coordinates", [])
            if not coordinates:
                return None

            # Extrair coordenadas baseado no tipo de geometria
            geom_type = geometry.get("type", "")

            if geom_type == "Polygon":
                # Coordenadas de polígono: [[[lon, lat], ...]]
                coords = coordinates[0]
            elif geom_type == "Rectangle" or geom_type == "MultiPoint":
                coords = coordinates
            else:
                # Tentar pegar todas as coordenadas possíveis
                coords = coordinates

            # Calcular bbox
            lons = [c[0] for c in coords if len(c) >= 2]
            lats = [c[1] for c in coords if len(c) >= 2]

            if not lons or not lats:
                return None

            return (min(lons), min(lats), max(lons), max(lats))

        except Exception as e:
            print(f"Erro ao extrair bbox: {e}")
            return None

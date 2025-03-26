import folium
from folium import LayerControl, FeatureGroup, Marker, Popup
from folium.plugins import Fullscreen
from shapely.wkb import loads as wkb_loads
from collections import defaultdict
from folium import Element

def generate_map(geodata):
    """
    Genera una mappa Folium con due livelli organizzati:
    - Storing Places: Punti basati su storing_place_location con tabella di popup e immagini.
    - Finding Spots: Punti basati su finding_spot_location con tabella di popup e immagini.
    Include un pannello di ricerca avanzata per query dettagliate sui campi del database.
    """
    # Crea una mappa centrata
    mymap = folium.Map(location=[41.8719, 12.5674], zoom_start=6)
    mymap.get_root().html.add_child(Element('<div id="map"></div>'))  # Aggiungi un ID alla mappa

    # Crea i gruppi per i due livelli
    storing_layer = FeatureGroup(name="Luoghi di conservazione", control=True)
    finding_layer = FeatureGroup(name="Luoghi di rinvenimento", control=True)

    # Organizza i dati per posizione
    storing_places = defaultdict(list)
    finding_spots = defaultdict(list)
    markers = []

    for obj in geodata:
        # Decodifica le geometrie
        storing_point = None
        finding_point = None

        if 'storing_place_location' in obj and obj['storing_place_location']:
            storing_point = wkb_loads(obj['storing_place_location'], hex=True)
        if 'finding_spot_location' in obj and obj['finding_spot_location']:
            finding_point = wkb_loads(obj['finding_spot_location'], hex=True)

        # Ignora punti con coordinate nulle o zero
        if storing_point and (storing_point.x != 0 and storing_point.y != 0):
            storing_places[(storing_point.y, storing_point.x)].append(obj)
            markers.append({"unique_id": obj['unique_id'], "latitude": storing_point.y, "longitude": storing_point.x})

        if finding_point and (finding_point.x != 0 and finding_point.y != 0):
            finding_spots[(finding_point.y, finding_point.x)].append(obj)
            markers.append({"unique_id": obj['unique_id'], "latitude": finding_point.y, "longitude": finding_point.x})

    # ... (resto del codice rimane invariato)

    # Funzione per costruire i popup
    def create_popup(objects, title):
        popup_content = """
        <div style='background-color:white; overflow:auto; max-height:500px; max-width:700px;'>
            <button onclick="this.parentElement.requestFullscreen()" style="float:right;">Fullscreen</button>
        """
        popup_content += f"<b>{title}</b><br><table border='1' style='width:100%;'>"
        popup_content += """
        <tr>
            <th>ID Unico</th><th>Cronologia</th><th>Forma</th><th>Luogo di Conservazione</th>
            <th>Luogo di Ritrovamento</th><th>Numero di Inventario</th><th>Fonte Bibliografica</th>
            <th>Dimensioni</th><th>Descrizione</th><th>Luogo di Produzione</th>
            <th>Tipologia</th><th>Riferimenti Bibliografici</th><th>Anse/manici</th>
            <th>Base/piede</th><th>Decorazione</th><th>Tecniche decorative</th>
            <th>Iconografia</th><th>Tecniche produttive</th>
            <th>Analisi Archeometriche</th><th>Tipo di Analisi</th>
            <th>Materie Prime</th><th>Provenienza</th><th>Altre Informazioni</th>
            <th>Bollo</th><th>Testo del Bollo</th>
        </tr>
        """
        for obj in objects:
            popup_content += f"""
            <tr>
                <td>{obj['unique_id']}</td><td>{obj.get('chronology', 'N/A')}</td><td>{obj.get('shape', 'N/A')}</td>
                <td>{obj.get('storing_place', 'N/A')}</td><td>{obj.get('finding_spot', 'N/A')}</td>
                <td>{obj.get('inventory_number', 'N/A')}</td><td>{obj.get('bibliographical_source', 'N/A')}</td>
                <td>{obj.get('dimensions', 'N/A')}</td><td>{obj.get('description', 'N/A')}</td>
                <td>{obj.get('production_place', 'N/A')}</td><td>{obj.get('typology', 'N/A')}</td>
                <td>{obj.get('bibliographic_references', 'N/A')}</td><td>{obj.get('handles', 'N/A')}</td>
                <td>{obj.get('foot', 'N/A')}</td><td>{obj.get('decoration', 'No' if not obj.get('decoration') else 'Yes')}</td>
                <td>{obj.get('decoration_techniques', 'N/A')}</td><td>{obj.get('iconography', 'N/A')}</td>
                <td>{obj.get('manufacturing_techniques', 'N/A')}</td><td>{obj.get('archaeometry_analyses', 'No' if not obj.get('archaeometry_analyses') else 'Yes')}</td>
                <td>{obj.get('type_of_analysis', 'N/A')}</td><td>{obj.get('raw_materials', 'N/A')}</td>
                <td>{obj.get('provenance', 'N/A')}</td><td>{obj.get('other_info', 'N/A')}</td>
                <td>{obj.get('stamp', 'No' if not obj.get('stamp') else 'Yes')}</td><td>{obj.get('stamp_text', 'N/A')}</td>
            </tr>
            """
            if obj.get('images'):
                popup_content += "<tr><td colspan='25'><b>Images:</b><br>"
                for image in obj['images']:
                    popup_content += f"<img src='https://raw.githubusercontent.com/francescatomei/capuan_bronzes_db_map/main/static/uploads/{image}' width='200' style='margin:5px;'><br>"
                popup_content += "</td></tr>"

        popup_content += "</table></div>"
        return popup_content

    # Crea i marker per storing places
    for (lat, lon), objects in storing_places.items():
        Marker(
            location=[lat, lon],
            popup=Popup(create_popup(objects, "Storing Place Objects"), max_width=700),
            tooltip="Storing Place",
            icon=folium.Icon(color="blue")
        ).add_to(storing_layer)

    # Crea i marker per finding spots
    for (lat, lon), objects in finding_spots.items():
        Marker(
            location=[lat, lon],
            popup=Popup(create_popup(objects, "Finding Spot Objects"), max_width=700),
            tooltip="Finding Spot",
            icon=folium.Icon(color="red")
        ).add_to(finding_layer)

    # Aggiungi i layer alla mappa
    storing_layer.add_to(mymap)
    finding_layer.add_to(mymap)

    # Aggiungi il controllo di layer e fullscreen
    LayerControl().add_to(mymap)
    Fullscreen().add_to(mymap)

    # Bottone della barra di ricerca
    search_button_html = f"""
    <div style="position: absolute; top: 10px; left: 60px; z-index: 1000;">
        <button onclick="toggleSearchPanel()" style="padding: 10px; background: #007bff; color: white; border: 1px solid #0056b3; border-radius: 5px; cursor: pointer;">Ricerca Avanzata</button>
    </div>
    <div id="search-panel" style="position: absolute; top: 60px; left: 10px; z-index: 1000; background: white; border: 1px solid #ccc; width: 300px; padding: 10px; display: none;">
        <h4>Ricerca Avanzata</h4>
        <form id="search-form" onsubmit="return false;">
            <input type="text" id="search-chronology" placeholder="Cronologia"><br>
            <input type="text" id="search-shape" placeholder="Forma"><br>
            <input type="text" id="search-storing_place" placeholder="Luogo di Conservazione"><br>
            <input type="text" id="search-finding_spot" placeholder="Luogo di Ritrovamento"><br>
            <input type="text" id="search-production_place" placeholder="Luogo di Produzione"><br>
            <input type="text" id="search-typology" placeholder="Tipologia"><br>
            <input type="text" id="search-handles" placeholder="Anse/manici"><br>
            <input type="text" id="search-foot" placeholder="Base/piede"><br>
            <input type="text" id="search-decoration" placeholder="Decorazione"><br>
            <input type="text" id="search-decoration-techniques" placeholder="Tecniche Decorative"><br>
            <input type="text" id="search-iconography" placeholder="Iconografia"><br>
            <input type="text" id="search-manufacturing-techniques" placeholder="Tecniche Produttive"><br>
            <input type="text" id="search-archaeometry-analyses" placeholder="Analisi Archeometriche"><br>
            <input type="text" id="search-type-of-analysis" placeholder="Tipo di Analisi"><br>
            <input type="text" id="search-stamp" placeholder="Bollo"><br>
            <input type="text" id="search-stamp-text" placeholder="Testo del Bollo"><br>
            <button onclick="executeSearch()">Cerca</button>
        </form>
        <div id="search-results" style="margin-top: 10px; max-height: 200px; overflow: auto;"></div>
    </div>
    <script>
        const markers = {markers};

        function toggleSearchPanel() {{
            const panel = document.getElementById('search-panel');
            panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
        }}

        function executeSearch() {{
            const filters = {{
                chronology: document.getElementById('search-chronology').value.trim(),
                shape: document.getElementById('search-shape').value.trim(),
                storing_place: document.getElementById('search-storing_place').value.trim(),
                finding_spot: document.getElementById('search-finding_spot').value.trim(),
                production_place: document.getElementById('search-production_place').value.trim(),
                typology: document.getElementById('search-typology').value.trim(),
                handles: document.getElementById('search-handles').value.trim(),
                foot: document.getElementById('search-foot').value.trim(),
                decoration: document.getElementById('search-decoration').value.trim(),
                decoration_techniques: document.getElementById('search-decoration-techniques').value.trim(),
                iconography: document.getElementById('search-iconography').value.trim(),
                manufacturing_techniques: document.getElementById('search-manufacturing-techniques').value.trim(),
                archaeometry_analyses: document.getElementById('search-archaeometry-analyses').value.trim(),
                type_of_analysis: document.getElementById('search-type-of-analysis').value.trim(),
                stamp: document.getElementById('search-stamp').value.trim(),
                stamp_text: document.getElementById('search-stamp-text').value.trim()
            }};

            fetch('/search', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify(filters)
            }})
            .then(response => response.json())
            .then(data => {{
                const resultsContainer = document.getElementById('search-results');
                resultsContainer.innerHTML = "<h5>Risultati:</h5>";

                if (data.length === 0) {{
                    resultsContainer.innerHTML += "<p>Nessun risultato trovato</p>";
                    return;
                }}

                let table = "<table border='1' style='width:100%;'>";
                table += `
                    <tr>
                        <th>ID Unico</th>
                        <th>Cronologia</th>
                        <th>Forma</th>
                        <th>Luogo di Conservazione</th>
                        <th>Luogo di Ritrovamento</th>
                        <th>Azioni</th>
                    </tr>
                `;

                data.forEach(obj => {{
                    table += `
                        <tr>
                            <td>${{obj.unique_id}}</td>
                            <td>${{obj.chronology || "N/A"}}</td>
                            <td>${{obj.shape || "N/A"}}</td>
                            <td>${{obj.storing_place || "N/A"}}</td>
                            <td>${{obj.finding_spot || "N/A"}}</td>
                            <td>
                                <button onclick="centerMap(${{obj.latitude}}, ${{obj.longitude}})">Mostra sulla mappa</button>
                            </td>
                        </tr>
                    `;
                }});

                table += "</table>";
                resultsContainer.innerHTML += table;
            }})
            .catch(error => console.error('Errore:', error));
        }}

        function centerMap(latitude, longitude) {{
            // Accedi alla mappa tramite l'ID
            const mapElement = document.getElementById('map');
            if (mapElement && mapElement._map) {{
                mapElement._map.setView([latitude, longitude], 15) // Zoom a 15
            }} else {{
                console.error("Mappa non trovata o non accessibile.");
            }}
        }}
    </script>
    """
    mymap.get_root().html.add_child(Element(search_button_html))

    return mymap
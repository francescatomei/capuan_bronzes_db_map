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
    - Separazione visiva tra record nei popup
    - Tooltip contestuali al passaggio del mouse
    Include un pannello di ricerca avanzata per query dettagliate sui campi del database.
    """
    # Crea una mappa centrata con impostazioni robuste
    mymap = folium.Map(
        location=[41.8719, 12.5674],
        zoom_start=6,
        tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        attr='OpenStreetMap',
        control_scale=True,
        height='100%',
        width='100%'
    )

    # Aggiungi stili CSS per garantire la visualizzazione corretta
    mymap.get_root().html.add_child(Element("""
    <style>
        html, body {
            height: 100%;
            margin: 0;
            padding: 0;
            overflow: hidden;
        }
        .folium-map {
            position: absolute !important;
            top: 0 !important;
            bottom: 0 !important;
            right: 0 !important;
            left: 0 !important;
            z-index: 1;
        }
        /* Stili per i popup */
        .popup-container {
            background-color: white;
            padding: 15px;
            max-width: 700px;
            max-height: 500px;
            overflow-y: auto;
        }
        .popup-title {
            text-align: center;
            margin-bottom: 15px;
            color: #333;
            font-size: 1.2em;
        }
        .popup-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
        }
        .popup-table th {
            background-color: #f2f2f2;
            text-align: left;
            padding: 8px;
            width: 30%;
        }
        .popup-table td {
            padding: 8px;
            border: 1px solid #ddd;
        }
        .popup-divider {
            margin: 20px 0;
            border-top: 2px dashed #ccc;
        }
        .popup-image {
            max-width: 200px;
            max-height: 200px;
            margin: 5px;
        }
        .search-container {
            position: absolute;
            top: 10px;
            left: 60px;
            z-index: 1000;
        }
        #search-panel {
            z-index: 1000;
            background: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.2);
            width: 300px;
            max-height: 80vh;
            overflow-y: auto;
        }
        .search-control {
            margin-bottom: 10px;
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .search-button {
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            width: 100%;
        }
        .search-button:hover {
            background: #0056b3;
        }
        .search-results {
            margin-top: 15px;
        }
        .search-results table {
            width: 100%;
            border-collapse: collapse;
        }
        .search-results th, .search-results td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        .search-results th {
            background-color: #f2f2f2;
        }
    </style>
    """))

    # Crea i gruppi per i due livelli
    storing_layer = FeatureGroup(name="Luoghi di conservazione", control=True)
    finding_layer = FeatureGroup(name="Luoghi di rinvenimento", control=True)

    # Organizza i dati per posizione
    storing_places = defaultdict(list)
    finding_spots = defaultdict(list)
    

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

    # Funzione per costruire i popup (mantenendo il formato originale)
    def create_popup(objects, title):
        popup_content = """
        <div class="popup-container">
            <button onclick="this.parentElement.requestFullscreen()" style="float:right;">Fullscreen</button>
            <div class="popup-title">{}</div>
        """.format(title)
        
        for i, obj in enumerate(objects):
            if i > 0:
                popup_content += '<div class="popup-divider"></div>'
                
            popup_content += """
            <table class="popup-table">
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
                <tr>
                    <td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td>
                    <td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td>
                    <td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td>
                    <td>{}</td><td>{}</td><td>{}</td><td>{}</td>
                </tr>
            """.format(
                obj.get('unique_id', 'N/A'),
                obj.get('chronology', 'N/A'),
                obj.get('shape', 'N/A'),
                obj.get('storing_place', 'N/A'),
                obj.get('finding_spot', 'N/A'),
                obj.get('inventory_number', 'N/A'),
                obj.get('bibliographical_source', 'N/A'),
                obj.get('dimensions', 'N/A'),
                obj.get('description', 'N/A'),
                obj.get('production_place', 'N/A'),
                obj.get('typology', 'N/A'),
                obj.get('bibliographic_references', 'N/A'),
                obj.get('handles', 'N/A'),
                obj.get('foot', 'N/A'),
                'No' if not obj.get('decoration') else 'Yes',
                obj.get('decoration_techniques', 'N/A'),
                obj.get('iconography', 'N/A'),
                obj.get('manufacturing_techniques', 'N/A'),
                'No' if not obj.get('archaeometry_analyses') else 'Yes',
                obj.get('type_of_analysis', 'N/A'),
                obj.get('raw_materials', 'N/A'),
                obj.get('provenance', 'N/A'),
                obj.get('other_info', 'N/A'),
                'No' if not obj.get('stamp') else 'Yes',
                obj.get('stamp_text', 'N/A')
            )
            
            if obj.get('images'):
                popup_content += """
                <tr>
                    <td colspan="25" style="text-align: center;">
                """
                for img in obj['images']:
                    img_url = img if img.startswith("http") else f"https://capuan-bronzes-db-map.onrender.com/static/uploads/{img}"
                    popup_content += f'<img src="{img_url}" class="popup-image">'
                popup_content += "</td></tr>"
            
            popup_content += "</table>"
        
        popup_content += "</div>"
        return popup_content

    # Aggiungi marker con tooltip personalizzati
    for (lat, lon), objs in storing_places.items():
        location_name = objs[0].get('storing_place', 'Luogo di conservazione')
        Marker(
            location=[lat, lon],
            popup=Popup(create_popup(objs, "Oggetti conservati in: " + location_name), max_width=750),
            tooltip=location_name,
            icon=folium.Icon(color="blue", icon="archive")
        ).add_to(storing_layer)

    for (lat, lon), objs in finding_spots.items():
        location_name = objs[0].get('finding_spot', 'Luogo di ritrovamento')
        Marker(
            location=[lat, lon],
            popup=Popup(create_popup(objs, "Oggetti rinvenuti in: " + location_name), max_width=750),
            tooltip=location_name,
            icon=folium.Icon(color="red", icon="search")
        ).add_to(finding_layer)

    # Aggiungi i layer alla mappa
    storing_layer.add_to(mymap)
    finding_layer.add_to(mymap)

    # Aggiungi il controllo di layer e fullscreen
    LayerControl().add_to(mymap)
    Fullscreen().add_to(mymap)

    # Bottone della barra di ricerca con TUTTI i parametri originali
    search_button_html = """
    <div class="search-container">
        <button onclick="toggleSearchPanel()" class="search-button">Ricerca Avanzata</button>
        <div id="search-panel" style="display: none;">
            <h4>Ricerca Avanzata</h4>
            <form id="search-form">
                <select id="search-chronology" class="search-control">
                    <option value="">Cronologia</option>
                    <option value="I sec. a.C.">I sec. a.C.</option>
                    <option value="I sec. d.C.">I sec. d.C.</option>
                    <option value="II sec. d.C.">II sec. d.C.</option>
                    <option value="III sec. d.C.">III sec. d.C.</option>
                </select>
                
                <select id="search-shape" class="search-control">
                    <option value="">Forma</option>
                    <option value="casseruola">Casseruola</option>
                    <option value="coppa a becco">Coppa a becco</option>
                    <option value="brocca">Brocca</option>
                    <option value="brocca monoansata">Brocca monoansata</option>
                    <option value="brocca a bocca trilobata">Brocca a bocca trilobata</option>
                    <option value="situla">Situla</option>
                    <option value="piede a forma di pelta">Piede a forma di pelta</option>
                    <option value="patera">Patera</option>
                    <option value="piede di situla">Piede di situla</option>
                    <option value="manico di casseruola">Manico di casseruola</option>
                    <option value="manico di patera">Manico di patera</option>
                    <option value="mestolo">Mestolo</option>
                    <option value="bacino">Bacino</option>
                    <option value="colino">Colino</option>
                    <option value="calderone">Calderone</option>
                </select>
                
                <input type="text" id="search-storing_place" class="search-control" placeholder="Luogo di Conservazione">
                <input type="text" id="search-finding_spot" class="search-control" placeholder="Luogo di Ritrovamento">
                <input type="text" id="search-production_place" class="search-control" placeholder="Luogo di Produzione">
                <input type="text" id="search-typology" class="search-control" placeholder="Tipologia">
                <input type="text" id="search-decoration_techniques" class="search-control" placeholder="Tecniche Decorative">
                <input type="text" id="search-iconography" class="search-control" placeholder="Iconografia">
                <input type="text" id="search-manufacturing_techniques" class="search-control" placeholder="Tecniche Produttive">
                <input type="text" id="search-type_of_analysis" class="search-control" placeholder="Tipo di Analisi">
                <input type="text" id="search-stamp_text" class="search-control" placeholder="Testo del Bollo">

                <div style="margin: 10px 0;">
                    <label style="display: block; margin: 5px 0;">
                        <input type="checkbox" id="search-decoration"> Decorazione
                    </label>
                    <label style="display: block; margin: 5px 0;">
                        <input type="checkbox" id="search-archaeometry_analyses"> Analisi Archeometriche
                    </label>
                    <label style="display: block; margin: 5px 0;">
                        <input type="checkbox" id="search-stamp"> Bollo
                    </label>
                </div>

                <button type="button" class="search-button" onclick="executeSearch()">Cerca</button>
            </form>

            <div id="search-results" class="search-results"></div>
        </div>
    </div>

    <script>
    // Variabile globale per la mappa
    var foliumMap;
    
    // Attendi che la mappa sia completamente caricata
    function initializeMap() {
        var mapElement = document.querySelector('.folium-map');
        if (mapElement && mapElement._map) {
            foliumMap = mapElement._map;
        } else {
            setTimeout(initializeMap, 100);
        }
    }
    
    document.addEventListener('DOMContentLoaded', function() {
        initializeMap();
    });

    function toggleSearchPanel() {
        const panel = document.getElementById('search-panel');
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    }

    function executeSearch() {
        const filters = {
            "chronology": document.getElementById('search-chronology').value.trim(),
            "shape": document.getElementById('search-shape').value.trim(),
            "storing_place": document.getElementById('search-storing_place').value.trim(),
            "finding_spot": document.getElementById('search-finding_spot').value.trim(),
            "production_place": document.getElementById('search-production_place').value.trim(),
            "typology": document.getElementById('search-typology').value.trim(),
            "decoration_techniques": document.getElementById('search-decoration_techniques').value.trim(),
            "iconography": document.getElementById('search-iconography').value.trim(),
            "manufacturing_techniques": document.getElementById('search-manufacturing_techniques').value.trim(),
            "type_of_analysis": document.getElementById('search-type_of_analysis').value.trim(),
            "stamp_text": document.getElementById('search-stamp_text').value.trim(),
            "decoration": document.getElementById('search-decoration').checked ? "true" : "false",
            "archaeometry_analyses": document.getElementById('search-archaeometry_analyses').checked ? "true" : "false",
            "stamp": document.getElementById('search-stamp').checked ? "true" : "false"
        };

        fetch('/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(filters)
        })
        .then(response => response.json())
        .then(data => {
            const resultsContainer = document.getElementById('search-results');
            resultsContainer.innerHTML = "<h5>Risultati:</h5>";

            if (data.length === 0) {
                resultsContainer.innerHTML += "<p>Nessun risultato trovato</p>";
                return;
            }

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

            data.forEach(obj => {
                table += `
                    <tr>
                        <td>${obj.unique_id}</td>
                        <td>${obj.chronology ? obj.chronology : "N/A"}</td>
                        <td>${obj.shape ? obj.shape : "N/A"}</td>
                        <td>${obj.storing_place ? obj.storing_place : "N/A"}</td>
                        <td>${obj.finding_spot ? obj.finding_spot : "N/A"}</td>
                        <td>
                            <button onclick="centerMap(${obj.latitude}, ${obj.longitude})" style="padding: 5px 10px; background: #007bff; color: white; border: none; border-radius: 3px; cursor: pointer;">Mostra sulla mappa</button>
                        </td>
                    </tr>
                `;
            });

            table += "</table>";
            resultsContainer.innerHTML += table;
        })
        .catch(error => console.error('Errore:', error));
    }

    function centerMap(latitude, longitude) {
        if (foliumMap) {
            foliumMap.setView([latitude, longitude], 15);
        } else {
            console.log("Mappa non ancora inizializzata, riprovo...");
            setTimeout(function() {
                centerMap(latitude, longitude);
            }, 100);
        }
    }
    </script>
    """
    mymap.get_root().html.add_child(Element(search_button_html))
    
    return mymap
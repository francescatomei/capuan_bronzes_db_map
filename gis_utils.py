import folium
from folium import LayerControl, FeatureGroup, Marker, Popup
from folium.plugins import Fullscreen
from shapely.wkb import loads as wkb_loads
from collections import defaultdict
from folium import Element

def generate_map(geodata):
    """
    Genera una mappa Folium completa con:
    - Popup completi e funzionanti
    - Evidenziazione marker corretta
    - Ricerca avanzata con tutti i parametri
    - Fix per l'errore '_marker' null
    """
    # Configurazione mappa base
    mymap = folium.Map(
        location=[41.8719, 12.5674],
        zoom_start=6,
        tiles='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        attr='OpenStreetMap',
        control_scale=True,
        height='100%',
        width='100%'
    )

    # Aggiungi stili CSS
    mymap.get_root().html.add_child(Element("""
    <style>
        html, body {
            height: 100%;
            margin: 0;
            padding: 0;
            overflow: hidden;
        }
        .folium-map {
            position: absolute;
            top: 0;
            bottom: 0;
            right: 0;
            left: 0;
            z-index: 1;
        }
        .search-container {
            position: absolute;
            top: 10px;
            left: 60px;
            z-index: 1000;
        }
        #search-panel {
            background: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.2);
            width: 300px;
            max-height: 80vh;
            overflow-y: auto;
            display: none;
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
        .highlighted-marker {
            filter: hue-rotate(120deg) brightness(1.2);
            transform: scale(1.3);
            transition: all 0.3s ease;
            z-index: 1000 !important;
        }
        .popup-content {
            max-width: 700px;
            max-height: 500px;
            overflow: auto;
            padding: 10px;
        }
        .popup-image {
            max-width: 200px;
            max-height: 200px;
            margin: 5px;
            display: block;
        }
        .popup-table {
            width: 100%;
            border-collapse: collapse;
        }
        .popup-table th, .popup-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        .popup-table th {
            background-color: #f2f2f2;
        }
    </style>
    """))

    # Inizializza layer e dizionario marker
    storing_layer = FeatureGroup(name="Luoghi di conservazione", show=True)
    finding_layer = FeatureGroup(name="Luoghi di rinvenimento", show=True)
    marker_dict = {}

    # Processa i dati geografici
    for obj in geodata:
        # Estrai geometrie
        storing_point = wkb_loads(obj['storing_place_location'], hex=True) if obj.get('storing_place_location') else None
        finding_point = wkb_loads(obj['finding_spot_location'], hex=True) if obj.get('finding_spot_location') else None

        # Crea marker per storing place
        if storing_point and storing_point.x != 0 and storing_point.y != 0:
            popup = Popup(create_popup_content(obj, "Luogo di conservazione"), max_width=700)
            marker = Marker(
                location=[storing_point.y, storing_point.x],
                popup=popup,
                icon=folium.Icon(color='blue'),
                tooltip=f"ID: {obj['unique_id']}"
            )
            marker.add_to(storing_layer)
            marker_dict[obj['unique_id']] = marker._id  # Memorizza l'ID Leaflet

        # Crea marker per finding spot
        if finding_point and finding_point.x != 0 and finding_point.y != 0:
            popup = Popup(create_popup_content(obj, "Luogo di ritrovamento"), max_width=700)
            marker = Marker(
                location=[finding_point.y, finding_point.x],
                popup=popup,
                icon=folium.Icon(color='red'),
                tooltip=f"ID: {obj['unique_id']}"
            )
            marker.add_to(finding_layer)
            marker_dict[obj['unique_id']] = marker._id  # Memorizza l'ID Leaflet

    # Aggiungi elementi alla mappa
    storing_layer.add_to(mymap)
    finding_layer.add_to(mymap)
    LayerControl().add_to(mymap)
    Fullscreen().add_to(mymap)

    # Bottone della barra di ricerca
    search_html = """
    <div class="search-container">
        <button onclick="toggleSearchPanel()" class="search-button">Ricerca Avanzata</button>
        <div id="search-panel">
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

                <div style="margin:10px 0;">
                    <label><input type="checkbox" id="search-decoration"> Decorazione</label><br>
                    <label><input type="checkbox" id="search-archaeometry"> Analisi archeometriche</label><br>
                    <label><input type="checkbox" id="search-stamp"> Bollo</label>
                </div>
                
                <button type="button" class="search-button" onclick="executeSearch()">Cerca</button>
            </form>
            
            <div id="search-results" style="margin-top:15px;"></div>
        </div>
    </div>
    """

    # Script per la gestione dei marker
    marker_script = f"""
    <script>
    // Dizionario globale per gli ID dei marker
    window.markerIds = {{
        {', '.join([f"'{k}': '{v}'" for k, v in marker_dict.items()])}
    }};
    
    let currentHighlighted = null;
    
    function toggleSearchPanel() {{
        const panel = document.getElementById('search-panel');
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    }}
    
    function getMarkerById(id) {{
        // Trova il marker usando l'ID Leaflet
        const leafletId = window.markerIds[id];
        if (!leafletId) return null;
        
        // Cerca il marker in tutti i layer della mappa
        const map = document.querySelector('.folium-map')._map;
        for (const layerId in map._layers) {{
            const layer = map._layers[layerId];
            if (layer._leaflet_id === leafletId) {{
                return layer;
            }}
        }}
        return null;
    }}
    
    function highlightMarker(markerId) {{
        // Rimuovi evidenziazione precedente
        if (currentHighlighted && currentHighlighted._icon) {{
            currentHighlighted._icon.classList.remove('highlighted-marker');
        }}
        
        // Trova e evidenzia il nuovo marker
        const marker = getMarkerById(markerId);
        if (marker && marker._icon) {{
            marker._icon.classList.add('highlighted-marker');
            marker.openPopup();
            currentHighlighted = marker;
            
            // Centra la mappa sul marker
            const map = marker._map;
            map.setView(marker.getLatLng(), map.getZoom());
        }}
    }}
    
    function executeSearch() {{
        const filters = {{
            chronology: document.getElementById('search-chronology').value,
            shape: document.getElementById('search-shape').value,
            storing_place: document.getElementById('search-storing_place').value,
            finding_spot: document.getElementById('search-finding_spot').value,
            production_place: document.getElementById('search-production_place').value,
            typology: document.getElementById('search-typology').value,
            decoration_techniques: document.getElementById('search-decoration_techniques').value,
            iconography: document.getElementById('search-iconography').value,
            manufacturing_techniques: document.getElementById('search-manufacturing_techniques').value,
            type_of_analysis: document.getElementById('search-type_of_analysis').value,
            stamp_text: document.getElementById('search-stamp_text').value,
            decoration: document.getElementById('search-decoration').checked,
            archaeometry: document.getElementById('search-archaeometry').checked,
            stamp: document.getElementById('search-stamp').checked
        }};
        
        fetch('/search', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify(filters)
        }})
        .then(response => response.json())
        .then(data => showResults(data))
        .catch(error => console.error('Error:', error));
    }}
    
    function showResults(data) {{
        const container = document.getElementById('search-results');
        if (!data || data.length === 0) {{
            container.innerHTML = '<p>Nessun risultato trovato</p>';
            return;
        }}
        
        let html = '<table style="width:100%"><tr><th>ID</th><th>Cronologia</th><th>Forma</th><th>Azioni</th></tr>';
        data.forEach(item => {{
            html += `<tr>
                <td>${{item.unique_id}}</td>
                <td>${{item.chronology || 'N/A'}}</td>
                <td>${{item.shape || 'N/A'}}</td>
                <td><button onclick="highlightMarker('${{item.unique_id}}')" style="padding:5px 10px;background:#007bff;color:white;border:none;border-radius:3px;cursor:pointer;">Mostra</button></td>
            </tr>`;
        }});
        html += '</table>';
        container.innerHTML = html;
    }}
    </script>
    """

    mymap.get_root().html.add_child(Element(search_html))
    mymap.get_root().html.add_child(Element(marker_script))
    
    return mymap

def create_popup_content(obj, title):
    """Crea contenuto popup completo con tutti i campi"""
    html = f"""
    <div class="popup-content">
        <button onclick="this.parentElement.requestFullscreen()" style="float:right;background:#007bff;color:white;border:none;padding:5px 10px;border-radius:3px;cursor:pointer;">Fullscreen</button>
        <h4>{title}</h4>
        <table class="popup-table">
            <tr><th>ID Unico:</th><td>{obj.get('unique_id', 'N/A')}</td></tr>
            <tr><th>Cronologia:</th><td>{obj.get('chronology', 'N/A')}</td></tr>
            <tr><th>Forma:</th><td>{obj.get('shape', 'N/A')}</td></tr>
            <tr><th>Luogo Conservazione:</th><td>{obj.get('storing_place', 'N/A')}</td></tr>
            <tr><th>Luogo Ritrovamento:</th><td>{obj.get('finding_spot', 'N/A')}</td></tr>
            <tr><th>Numero Inventario:</th><td>{obj.get('inventory_number', 'N/A')}</td></tr>
            <tr><th>Fonte Bibliografica:</th><td>{obj.get('bibliographical_source', 'N/A')}</td></tr>
            <tr><th>Dimensioni:</th><td>{obj.get('dimensions', 'N/A')}</td></tr>
            <tr><th>Descrizione:</th><td>{obj.get('description', 'N/A')}</td></tr>
            <tr><th>Luogo Produzione:</th><td>{obj.get('production_place', 'N/A')}</td></tr>
            <tr><th>Tipologia:</th><td>{obj.get('typology', 'N/A')}</td></tr>
            <tr><th>Riferimenti Bibliografici:</th><td>{obj.get('bibliographic_references', 'N/A')}</td></tr>
            <tr><th>Anse/manici:</th><td>{obj.get('handles', 'N/A')}</td></tr>
            <tr><th>Base/piede:</th><td>{obj.get('foot', 'N/A')}</td></tr>
            <tr><th>Decorazione:</th><td>{'Sì' if obj.get('decoration') else 'No'}</td></tr>
            <tr><th>Tecniche decorative:</th><td>{obj.get('decoration_techniques', 'N/A')}</td></tr>
            <tr><th>Iconografia:</th><td>{obj.get('iconography', 'N/A')}</td></tr>
            <tr><th>Tecniche produttive:</th><td>{obj.get('manufacturing_techniques', 'N/A')}</td></tr>
            <tr><th>Analisi Archeometriche:</th><td>{'Sì' if obj.get('archaeometry_analyses') else 'No'}</td></tr>
            <tr><th>Tipo di Analisi:</th><td>{obj.get('type_of_analysis', 'N/A')}</td></tr>
            <tr><th>Materie Prime:</th><td>{obj.get('raw_materials', 'N/A')}</td></tr>
            <tr><th>Provenienza:</th><td>{obj.get('provenance', 'N/A')}</td></tr>
            <tr><th>Altre Informazioni:</th><td>{obj.get('other_info', 'N/A')}</td></tr>
            <tr><th>Bollo:</th><td>{'Sì' if obj.get('stamp') else 'No'}</td></tr>
            <tr><th>Testo del Bollo:</th><td>{obj.get('stamp_text', 'N/A')}</td></tr>
        </table>
    """

    # Aggiungi immagini se presenti
    if obj.get('images'):
        html += "<div style='margin-top:15px;text-align:center;'>"
        for img in obj['images']:
            img_url = img if img.startswith('http') else f"https://capuan-bronzes-db-map.onrender.com/static/uploads/{img}"
            html += f"<img src='{img_url}' class='popup-image'>"
        html += "</div>"
    
    html += "</div>"
    return html
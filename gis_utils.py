import folium
from folium import LayerControl, FeatureGroup, Marker, Popup
from folium.plugins import Fullscreen
from shapely.wkb import loads as wkb_loads
from collections import defaultdict
from folium import Element

def generate_map(geodata):
    """
    Genera una mappa Folium completa con:
    - Due layer separati per luoghi di conservazione e ritrovamento
    - Ricerca avanzata con tutti i parametri
    - Evidenziazione marker al posto del centramento
    - Gestione delle immagini nei popup
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
        .popup-image {
            max-width: 200px;
            max-height: 200px;
            margin: 5px;
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
            marker = Marker(
                location=[storing_point.y, storing_point.x],
                popup=create_popup_content(obj, "Luogo di conservazione"),
                icon=folium.Icon(color='blue'),
                tooltip=f"ID: {obj['unique_id']}"
            )
            marker.add_to(storing_layer)
            marker_dict[obj['unique_id']] = marker

        # Crea marker per finding spot
        if finding_point and finding_point.x != 0 and finding_point.y != 0:
            marker = Marker(
                location=[finding_point.y, finding_point.x],
                popup=create_popup_content(obj, "Luogo di ritrovamento"),
                icon=folium.Icon(color='red'),
                tooltip=f"ID: {obj['unique_id']}"
            )
            marker.add_to(finding_layer)
            marker_dict[obj['unique_id']] = marker

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
    marker_script = """
    <script>
    // Dizionario globale dei marker
    window.markerDict = {
        %s
    };
    
    let currentHighlighted = null;
    
    function toggleSearchPanel() {
        const panel = document.getElementById('search-panel');
        panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    }
    
    function highlightMarker(id) {
        // Rimuovi evidenziazione precedente
        if (currentHighlighted && currentHighlighted._icon) {
            currentHighlighted._icon.classList.remove('highlighted-marker');
        }
        
        // Evidenzia nuovo marker
        const marker = window.markerDict[id];
        if (marker && marker._icon) {
            marker._icon.classList.add('highlighted-marker');
            marker.openPopup();
            currentHighlighted = marker;
        }
    }
    
    function executeSearch() {
        const filters = {
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
        };
        
        fetch('/search', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(filters)
        })
        .then(response => response.json())
        .then(data => showResults(data))
        .catch(error => console.error('Error:', error));
    }
    
    function showResults(data) {
        const container = document.getElementById('search-results');
        if (!data || data.length === 0) {
            container.innerHTML = '<p>Nessun risultato trovato</p>';
            return;
        }
        
        let html = '<table style="width:100%%"><tr><th>ID</th><th>Cronologia</th><th>Azioni</th></tr>';
        data.forEach(item => {
            html += `<tr>
                <td>${item.unique_id}</td>
                <td>${item.chronology || 'N/A'}</td>
                <td><button onclick="highlightMarker('${item.unique_id}')">Mostra</button></td>
            </tr>`;
        });
        html += '</table>';
        container.innerHTML = html;
    }
    </script>
    """ % ",\n        ".join([f"'{k}': document.querySelector('div[data-marker-id=\"{k}\"]')._marker" 
                           for k in marker_dict.keys()])

    # Aggiungi attributi identificativi ai marker
    for marker_id, marker in marker_dict.items():
        marker.options['data-marker-id'] = marker_id

    mymap.get_root().html.add_child(Element(search_html))
    mymap.get_root().html.add_child(Element(marker_script))
    
    return mymap

def create_popup_content(obj, title):
    """Crea il contenuto HTML per i popup dei marker"""
    html = f"""
    <div style="max-width:300px;max-height:400px;overflow:auto;">
        <h4>{title}</h4>
        <p><strong>ID:</strong> {obj['unique_id']}</p>
        <p><strong>Cronologia:</strong> {obj.get('chronology', 'N/A')}</p>
        <p><strong>Luogo conservazione:</strong> {obj.get('storing_place', 'N/A')}</p>
        <p><strong>Luogo ritrovamento:</strong> {obj.get('finding_spot', 'N/A')}</p>
    """
    
    # Aggiungi immagini se presenti
    if obj.get('images'):
        html += "<div style='margin-top:10px;'>"
        for img in obj['images']:
            img_url = img if img.startswith('http') else f"https://capuan-bronzes-db-map.onrender.com/static/uploads/{img}"
            html += f"<img src='{img_url}' class='popup-image'><br>"
        html += "</div>"
    
    html += "</div>"
    return html
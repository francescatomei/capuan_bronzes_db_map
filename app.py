from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from flask import jsonify
from werkzeug.utils import secure_filename
import os
from sqlalchemy import text
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from geoalchemy2 import Geometry
from geoalchemy2.elements import WKTElement
from db_utils import init_session, get_geodata
from gis_utils import generate_map

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = 'una_chiave_segreta_molto_sicura'

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:bronzi_capuani_db@db.aaakrbnlkgljvaksjxvv.supabase.co:5432/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # Folder for uploading files
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Max upload size: 16MB
db = SQLAlchemy(app)
ma = Marshmallow(app)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Models
class images(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    path = db.Column(db.String(255), nullable=False)
    archaeological_object_id = db.Column(db.Integer, db.ForeignKey('archaeological_objects.id'), nullable=False)
    archaeological_object = db.relationship('ArchaeologicalObject', back_populates='images')

class ArchaeologicalObject(db.Model):
    __tablename__ = 'archaeological_objects'
    id = db.Column(db.Integer, primary_key=True)
    unique_id = db.Column(db.String(50))
    chronology = db.Column(db.String(255))
    shape = db.Column(db.String(255))
    storing_place = db.Column(db.String(255))
    finding_spot = db.Column(db.String(255))
    storing_place_id = db.Column(db.Integer)
    finding_spot_id = db.Column(db.Integer)
    inventory_number = db.Column(db.String(50))
    bibliographical_source = db.Column(db.String(255))
    dimensions = db.Column(db.String(255))
    description = db.Column(db.String(255))
    production_place = db.Column(db.String(255))
    typology = db.Column(db.String(255))
    bibliographic_references = db.Column(db.String(255))
    handles = db.Column(db.String(255))
    foot = db.Column(db.String(255))
    decoration = db.Column(db.Boolean)
    decoration_techniques = db.Column(db.String(255))
    iconography = db.Column(db.String(255))
    manufacturing_techniques = db.Column(db.String(255))
    archaeometry_analyses = db.Column(db.Boolean)
    type_of_analysis = db.Column(db.String(255))
    raw_materials = db.Column(db.String(255))
    provenance = db.Column(db.String(255))
    other_info = db.Column(db.String(255))
    stamp = db.Column(db.Boolean)
    stamp_text = db.Column(db.String(255))
    longitude_storing_place = db.Column(db.Float, nullable=True)
    latitude_storing_place = db.Column(db.Float, nullable=True)
    longitude_finding_spot = db.Column(db.Float, nullable=True)
    latitude_finding_spot = db.Column(db.Float, nullable=True)
    storing_place_location = db.Column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    finding_spot_location = db.Column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    images = db.relationship('images', back_populates='archaeological_object')

@app.route('/add_object', methods=['POST'])
def add_object():
    # Extract form data
    data = request.form.to_dict()
    decoration = bool(data.get('decoration', False))
    archaeometry_analyses = bool(data.get('archaeometry_analyses', False))
    stamp = bool(data.get('stamp', False))
    longitude_storing_place = float(data.get('longitude_storing_place', 0)) if data.get('longitude_storing_place') else None
    latitude_storing_place = float(data.get('latitude_storing_place', 0)) if data.get('latitude_storing_place') else None
    longitude_finding_spot = float(data.get('longitude_finding_spot', 0)) if data.get('longitude_finding_spot') else None
    latitude_finding_spot = float(data.get('latitude_finding_spot', 0)) if data.get('latitude_finding_spot') else None

    # Create a new ArchaeologicalObject instance
    new_object = ArchaeologicalObject(
        unique_id=data.get('unique_id', ''),
        chronology=data.get('chronology', ''),
        shape=data.get('shape', ''),
        storing_place=data.get('storing_place', ''),
        finding_spot=data.get('finding_spot', ''),
        storing_place_id=int(data.get('storing_place_id', 0)) if data.get('storing_place_id') else None,
        finding_spot_id=int(data.get('finding_spot_id', 0)) if data.get('finding_spot_id') else None,
        inventory_number=data.get('inventory_number', ''),
        bibliographical_source=data.get('bibliographical_source', ''),
        dimensions=data.get('dimensions', ''),
        description=data.get('description', ''),
        production_place=data.get('production_place', ''),
        typology=data.get('typology', ''),
        bibliographic_references=data.get('bibliographic_references', ''),
        handles=data.get('handles', ''),
        foot=data.get('foot', ''),
        decoration=decoration,
        decoration_techniques=data.get('decoration_techniques', ''),
        iconography=data.get('iconography', ''),
        manufacturing_techniques=data.get('manufacturing_techniques', ''),
        archaeometry_analyses=archaeometry_analyses,
        type_of_analysis=data.get('type_of_analysis', ''),
        raw_materials=data.get('raw_materials', ''),
        provenance=data.get('provenance', ''),
        other_info=data.get('other_info', ''),
        stamp=stamp,
        stamp_text=data.get('stamp_text', ''),
        longitude_storing_place=longitude_storing_place,
        latitude_storing_place=latitude_storing_place,
        longitude_finding_spot=longitude_finding_spot,
        latitude_finding_spot=latitude_finding_spot,
        storing_place_location=WKTElement(f"POINT({longitude_storing_place} {latitude_storing_place})", srid=4326) if longitude_storing_place and latitude_storing_place else None,
        finding_spot_location=WKTElement(f"POINT({longitude_finding_spot} {latitude_finding_spot})", srid=4326) if longitude_finding_spot and latitude_finding_spot else None
    )

    db.session.add(new_object)
    db.session.commit()

    # Handle images upload
    if 'images' in request.files:
        files = request.files.getlist('images')
        for file in files:
            if file and file.filename:
                # Secure the filename and save to the upload folder
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(file_path)

               
                # Save the image path to the database
                new_image = images(
                    path=filename,  # Save normalized relative path
                    archaeological_object_id=new_object.id
                )
                db.session.add(new_image)
        db.session.commit()

    return redirect(url_for('home'))

@app.route('/')
def home():
    return render_template('form.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/view_data')
def view_data():
    archaeological_objects = ArchaeologicalObject.query.all()
    images_data = images.query.all()
    return render_template('view_data.html', archaeological_objects=archaeological_objects, images=images_data)

@app.route('/edit_object/<int:id>', methods=['GET', 'POST'])
def edit_object(id):
    # Recupera l'oggetto dal database
    obj = ArchaeologicalObject.query.get_or_404(id)
    
    if request.method == 'POST':
        # Aggiorna i campi con i dati ricevuti dal form
        obj.unique_id = request.form.get('unique_id', obj.unique_id)
        obj.chronology = request.form.get('chronology', obj.chronology)
        obj.shape = request.form.get('shape', obj.shape)
        obj.storing_place = request.form.get('storing_place', obj.storing_place)
        obj.finding_spot = request.form.get('finding_spot', obj.finding_spot)
        obj.storing_place_id = int(request.form.get('storing_place_id', obj.storing_place_id) or 0)
        obj.finding_spot_id = int(request.form.get('finding_spot_id', obj.finding_spot_id) or 0)
        obj.inventory_number = request.form.get('inventory_number', obj.inventory_number)
        obj.bibliographical_source = request.form.get('bibliographical_source', obj.bibliographical_source)
        obj.dimensions = request.form.get('dimensions', obj.dimensions)
        obj.description = request.form.get('description', obj.description)
        obj.production_place = request.form.get('production_place', obj.production_place)
        obj.typology = request.form.get('typology', obj.typology)
        obj.bibliographic_references = request.form.get('bibliographic_references', obj.bibliographic_references)
        obj.handles = request.form.get('handles', obj.handles)
        obj.foot = request.form.get('foot', obj.foot)
        obj.decoration = bool(request.form.get('decoration', obj.decoration))
        obj.decoration_techniques = request.form.get('decoration_techniques', obj.decoration_techniques)
        obj.iconography = request.form.get('iconography', obj.iconography)
        obj.manufacturing_techniques = request.form.get('manufacturing_techniques', obj.manufacturing_techniques)
        obj.archaeometry_analyses = bool(request.form.get('archaeometry_analyses', obj.archaeometry_analyses))
        obj.type_of_analysis = request.form.get('type_of_analysis', obj.type_of_analysis)
        obj.raw_materials = request.form.get('raw_materials', obj.raw_materials)
        obj.provenance = request.form.get('provenance', obj.provenance)
        obj.other_info = request.form.get('other_info', obj.other_info)
        obj.stamp = bool(request.form.get('stamp', obj.stamp))
        obj.stamp_text = request.form.get('stamp_text', obj.stamp_text)
        obj.longitude_storing_place = float(request.form.get('longitude_storing_place', obj.longitude_storing_place) or 0)
        obj.latitude_storing_place = float(request.form.get('latitude_storing_place', obj.latitude_storing_place) or 0)
        obj.longitude_finding_spot = float(request.form.get('longitude_finding_spot', obj.longitude_finding_spot) or 0)
        obj.latitude_finding_spot = float(request.form.get('latitude_finding_spot', obj.latitude_finding_spot) or 0)

        # Calcola e aggiorna le geometrie (se coordinate valide sono fornite)
        if obj.longitude_storing_place and obj.latitude_storing_place:
            obj.storing_place_location = f"POINT({obj.longitude_storing_place} {obj.latitude_storing_place})"
        else:
            obj.storing_place_location = None
        
        if obj.longitude_finding_spot and obj.latitude_finding_spot:
            obj.finding_spot_location = f"POINT({obj.longitude_finding_spot} {obj.latitude_finding_spot})"
        else:
            obj.finding_spot_location = None

        # Salva le modifiche nel database
        db.session.commit()
        return redirect(url_for('view_data'))

    # Renderizza il form di modifica precompilato con i valori attuali
    return render_template('edit_object.html', obj=obj)

@app.route('/delete_image/<int:image_id>', methods=['POST'])
def delete_image(image_id):
    session = db.session
    try:
        image = session.get(images, image_id)
        if not image:
            flash('Image not found', 'error')
            return redirect(url_for('view_data'))

        # Costruisci il percorso completo dell'immagine
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], image.path)
        
        # Elimina il file fisico se esiste
        if os.path.exists(file_path):
            os.remove(file_path)

        # Rimuovi l'immagine dal database
        session.delete(image)
        session.commit()
        flash('Image deleted successfully', 'success')

    except Exception as e:
        session.rollback()
        flash(f'Error deleting image: {str(e)}', 'error')

    finally:
        session.close()

    return redirect(url_for('view_data'))

@app.route('/add_image/<int:object_id>', methods=['POST'])
def add_image(object_id):
    if 'new_image' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('view_data'))

    file = request.files['new_image']

    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('view_data'))

    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Usa SQLAlchemy per gestire la connessione e salvare il record nel database
            session = db.session
            new_image = images(
                path=filename,
                archaeological_object_id=object_id
            )
            session.add(new_image)
            session.commit()

            flash('Image uploaded successfully', 'success')

        except Exception as e:
            session.rollback()
            flash(f'Error uploading image: {str(e)}', 'error')

        finally:
            session.close()
    else:
        flash('Invalid file format', 'error')

    return redirect(url_for('view_data'))

@app.route('/upload_image/<int:object_id>', methods=['POST'])
def upload_image(object_id):
    if 'image' not in request.files:
        return jsonify({'error': 'Nessun file selezionato'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'Nessun file selezionato'}), 400

    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Aggiunge l'immagine nel database
            new_image = images(
                path=filename,
                archaeological_object_id=object_id
            )
            db.session.add(new_image)
            db.session.commit()
            return jsonify({'success': 'Immagine caricata con successo', 'image_path': filename})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Formato file non valido'}), 400



@app.route('/map')
def map_view():
    session = db.session
    try:
        geodata = get_geodata(session)
        mymap = generate_map(geodata)
        mymap.save("templates/map.html")
    finally:
        session.close()
    return render_template("map.html")

from sqlalchemy.sql import text

@app.route('/search', methods=['POST'])
def search():
    session = db.session
    try:
        # Estrai i filtri dal corpo della richiesta
        filters = request.get_json()
        if not isinstance(filters, dict):
            return jsonify({'error': 'Invalid input format, expected JSON object'}), 400

        # Costruisci la query dinamica
        query = "SELECT * FROM archaeological_objects WHERE 1=1"
        params = {}

        for field, value in filters.items():
            if field in ['decoration', 'archaeometry_analyses', 'stamp']:  # Campi booleani
                # Converti valori booleani da stringhe a True/False
                if value.lower() in ['sì', 'true', 'yes']:
                    value = True
                elif value.lower() in ['no', 'false']:
                    value = False
                else:
                    return jsonify({'error': f"Invalid value for boolean field '{field}': {value}"}), 400
                
                query += f" AND {field} = :{field}"
                params[field] = value
            else:
                # Per altri campi, usa una ricerca parziale
                query += f" AND {field} ILIKE :{field}"
                params[field] = f"%{value}%"

        # Esegui la query
        results = session.execute(text(query), params).fetchall()
        data = [dict(row) for row in results]

        return jsonify(data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        session.close()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("Tabelle create con successo.")
    app.run(host='0.0.0.0', port=5000, debug=True)
"""
db_utils.py

Questo modulo contiene funzioni per interagire con il database PostgreSQL,
incluse operazioni per recuperare dati geografici.
"""
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from shapely.wkb import loads as wkb_loads

# Configurazione del database
DATABASE_URL = 'postgresql+psycopg://capuan_bronzes_owner:npg_r6HTmaW9XPOg@ep-morning-frost-a2jog6ch-pooler.eu-central-1.aws.neon.tech/capuan_bronzes?sslmode=require'
UPLOAD_FOLDER = 'C:/Users/franc/Projects/archaeology_project/static/uploads'

# Creazione del motore e del sessionmaker
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def init_session():
    """
    Inizializza e restituisce una nuova sessione del database.
    """
    return Session()

def get_geodata(session):
    try:
        query = text("""
            SELECT 
                ao.id,
                ao.unique_id,
                ao.chronology,
                ao.shape,
                ao.storing_place,
                ao.finding_spot,
                ao.inventory_number,
                ao.bibliographical_source,
                ao.dimensions,
                ao.description,
                ao.production_place,
                ao.typology,
                ao.bibliographic_references,
                ao.handles,
                ao.foot,
                ao.decoration,
                ao.decoration_techniques,
                ao.iconography,
                ao.manufacturing_techniques,
                ao.archaeometry_analyses,
                ao.type_of_analysis,
                ao.raw_materials,
                ao.provenance,
                ao.other_info,
                ao.stamp,
                ao.stamp_text,
                ST_AsEWKB(ao.storing_place_location) AS storing_place_location,
                ST_AsEWKB(ao.finding_spot_location) AS finding_spot_location,
                img.path AS image_path
            FROM archaeological_objects ao
            LEFT JOIN images img ON ao.id = img.archaeological_object_id
        """)

        results = session.execute(query).mappings().fetchall()

        geodata = []
        for row in results:
            obj = {
                "id": row["id"],
                "unique_id": row["unique_id"],
                "chronology": row["chronology"],
                "shape": row["shape"],
                "storing_place": row["storing_place"],
                "finding_spot": row["finding_spot"],
                "inventory_number": row["inventory_number"],
                "bibliographical_source": row["bibliographical_source"],
                "dimensions": row["dimensions"],
                "description": row["description"],
                "production_place": row["production_place"],
                "typology": row["typology"],
                "bibliographic_references": row["bibliographic_references"],
                "handles": row["handles"],
                "foot": row["foot"],
                "decoration": "Si" if row["decoration"] else "No",
                "decoration_techniques": row["decoration_techniques"],
                "iconography": row["iconography"],
                "manufacturing_techniques": row["manufacturing_techniques"],
                "archaeometry_analyses": "Si" if row["archaeometry_analyses"] else "No",
                "type_of_analysis": row["type_of_analysis"],
                "raw_materials": row["raw_materials"],
                "provenance": row["provenance"],
                "other_info": row["other_info"],
                "stamp": "Si" if row["stamp"] else "No",
                "stamp_text": row["stamp_text"],
                "storing_place_location": row["storing_place_location"].hex() if row["storing_place_location"] else None,
                "finding_spot_location": row["finding_spot_location"].hex() if row["finding_spot_location"] else None,
            }

            # Gestisci le immagini
            image_path = row["image_path"]
            if image_path:
                full_image_path = os.path.join(UPLOAD_FOLDER, image_path)
                if os.path.exists(full_image_path):
                    obj.setdefault("images", []).append(image_path)

            geodata.append(obj)

        return geodata
    finally:
        session.close()

if __name__ == "__main__":
    # Test del recupero dei dati
    session = init_session()
    try:
        # Recupero senza filtri
        geodata = get_geodata(session)
        print(f"Trovati {len(geodata)} oggetti senza filtri.")

        # Recupero con filtri
        filters = {"storing_place": "%Rome%"}
        filtered_data = get_geodata(session, filters)
        print(f"Trovati {len(filtered_data)} oggetti con filtri.")
    finally:
        session.close()

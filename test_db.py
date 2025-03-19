from app import db

def test_connection():
    try:
        with db.engine.connect() as connection:
            result = connection.execute("SELECT COUNT(*) FROM archaeological_objects")
            count = result.fetchone()[0]
            print(f"Totale record nella tabella archaeological_objects: {count}")
    except Exception as e:
        print(f"Errore di connessione al database: {e}")

if __name__ == "__main__":
    test_connection()

from database import get_db_connection

def insert_user(email, password):
    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        conn.close()

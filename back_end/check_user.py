from database import get_db_connection

def check_user(email, password):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password)).fetchone()
    conn.close()
    return user is not None

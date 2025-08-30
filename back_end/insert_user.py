# insert_user.py
from database import get_conn
from werkzeug.security import generate_password_hash
import sqlite3

def insert_user(email, password):
    """
    Insert a new user with hashed password.
    Returns:
        True if inserted successfully,
        False if user already exists or on error.
    """
    try:
        hashed_pw = generate_password_hash(password)
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)",
                (email.lower(), hashed_pw)
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Email already exists
        return False
    except sqlite3.OperationalError as e:
        print("DB operation error:", e)
        return False
    except Exception as e:
        print("Unexpected insert error:", e)
        return False

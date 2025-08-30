# database.py
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

DB_FILE = Path(__file__).with_name("users.db")
SQLITE_TIMEOUT = 10  # seconds, prevents 'database is locked' errors


def get_db_connection():
    """Return a sqlite3 connection with row_factory and timeout."""
    conn = sqlite3.connect(DB_FILE, timeout=SQLITE_TIMEOUT)
    conn.row_factory = sqlite3.Row
    return conn


# Alias used in app
def get_conn():
    return get_db_connection()


def _ensure_columns(conn):
    """Add missing columns if they don't exist (safe migration)."""
    try:
        conn.execute("ALTER TABLE users ADD COLUMN reset_token TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        conn.execute("ALTER TABLE users ADD COLUMN reset_expires INTEGER")
    except sqlite3.OperationalError:
        pass


def init_db():
    """Create users table and ensure migration columns exist."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        """)
        _ensure_columns(conn)
        conn.commit()


# ----------------- DB Operations -----------------
def insert_user(email, password):
    """Insert a new user. Returns True if successful, False if email exists."""
    hashed_pw = generate_password_hash(password)
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)",
                (email.lower(), hashed_pw)
            )
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except sqlite3.OperationalError as e:
        print("Insert error:", e)
        return False


def check_user(email, password):
    """Check user credentials."""
    try:
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT password FROM users WHERE email = ?", (email.lower(),))
            row = cur.fetchone()
            if not row:
                return False

            db_pass = row["password"]
            # Always check with werkzeug (only hashed passwords expected)
            return check_password_hash(db_pass, password)

    except sqlite3.OperationalError as e:
        print("Check error:", e)
        return False


def update_password(email, new_password):
    """Update password with hash for a given user."""
    hashed_pw = generate_password_hash(new_password)
    try:
        with get_db_connection() as conn:
            conn.execute("UPDATE users SET password=? WHERE email=?", (hashed_pw, email.lower()))
            conn.commit()
        return True
    except sqlite3.OperationalError as e:
        print("Update password error:", e)
        return False


if __name__ == "__main__":
    init_db()
    print("✅ DB initialized at", DB_FILE)

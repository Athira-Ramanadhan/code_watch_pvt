import sqlite3
from pathlib import Path

# Path to your database file
DB_FILE = Path(__file__).with_name("users.db")

# Admin details
ADMIN_NAME = "System Admin"
ADMIN_EMAIL = "admin@example.com"
ADMIN_HASHED_PASSWORD = "scrypt:32768:8:1$uw1rv732GK2Bd8AQ$76ce1ac47f0ae97e9eeac88078c780c34da3bdb5745f82b4c7b4f40041e3d9d5f325f70a1cb83ba6abdd4f5eda76d426570fc69091c43631750b20983c998890"
ADMIN_ROLE = "admin"

def insert_admin():
    try:
        # Open DB with timeout (waits if locked)
        conn = sqlite3.connect(DB_FILE, timeout=10)
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            (ADMIN_NAME, ADMIN_EMAIL, ADMIN_HASHED_PASSWORD, ADMIN_ROLE),
        )

        conn.commit()
        conn.close()
        print(f"✅ Admin inserted: {ADMIN_EMAIL}")

    except sqlite3.IntegrityError:
        print("⚠️ Admin already exists in the database.")
    except sqlite3.OperationalError as e:
        print("❌ Database error:", e)

if __name__ == "__main__":
    insert_admin()

import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

# Path to your users.db file
DB_FILE = Path(__file__).with_name("users.db")

# Admin details
ADMIN_EMAIL = "admin@example.com"
NEW_PASSWORD = "Admin@123"   # 👈 change this to anything you like

def reset_admin_password():
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()

        # Hash new password
        hashed_pw = generate_password_hash(NEW_PASSWORD)

        # Update password for admin
        cur.execute(
            "UPDATE users SET password=? WHERE email=? AND role='admin'",
            (hashed_pw, ADMIN_EMAIL)
        )

        if cur.rowcount == 0:
            print("⚠️ No admin user found. Did you create one yet?")
        else:
            conn.commit()
            print(f"✅ Admin password reset successfully! New password is: {NEW_PASSWORD}")

        conn.close()
    except Exception as e:
        print("❌ Error:", e)

if __name__ == "__main__":
    reset_admin_password()

import smtplib
from email.message import EmailMessage
from database import get_db_connection

def send_reset_email(to_email):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email=?", (to_email,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return False  # Email doesn't exist

    # Simulate token (in real app, use JWT or UUID + expiry)
    reset_link = f"http://localhost:3000/reset-password?email={to_email}"

    # Email content
    msg = EmailMessage()
    msg['Subject'] = 'Password Reset - CodeWatch'
    msg['From'] = 'your_email@example.com'  # Replace with your email
    msg['To'] = to_email
    msg.set_content(f"Click the link to reset your password:\n\n{reset_link}")

    try:
        # SMTP setup (Gmail example - enable 'less secure apps' or use App Passwords)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login('your_email@example.com', 'your_password')  # Replace with actual credentials
            smtp.send_message(msg)
        return True
    except Exception as e:
        print("Email sending failed:", e)
        return False

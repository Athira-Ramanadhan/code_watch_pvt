import smtplib
from email.mime.text import MIMEText
from flask import Flask, request, jsonify

app = Flask(__name__)

MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USERNAME = "athiraramanadh16@gmail.com"
MAIL_PASSWORD = "ukkhzufdfhgtfeul"   # App Password

def send_reset_email(to_email, reset_link):
    msg = MIMEText(f"Click this link to reset your password: {reset_link}")
    msg["Subject"] = "Password Reset Request"
    msg["From"] = MAIL_USERNAME
    msg["To"] = to_email

    try:
        with smtplib.SMTP(MAIL_SERVER, MAIL_PORT) as server:
            server.starttls()
            server.login(MAIL_USERNAME, MAIL_PASSWORD)
            server.sendmail(MAIL_USERNAME, [to_email], msg.as_string())
        return True
    except Exception as e:
        print("Error sending email:", e)
        return False

@app.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.json
    email = data.get("email")

    # Here, you’d usually check if the email exists in your DB
    reset_link = f"http://localhost:3000/reset-password?email={email}"  

    if send_reset_email(email, reset_link):
        return jsonify({"status": "success", "message": "Reset link sent to your email"})
    else:
        return jsonify({"status": "error", "message": "Could not send email"})

if __name__ == "__main__":
    app.run(debug=True)

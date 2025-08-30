import smtplib

MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USERNAME ="athiraramanadh16@gmail.com"
MAIL_PASSWORD = "ukkhzufdfhgtfeul"   # use 16-char App Password

print("Testing SMTP connection to", MAIL_SERVER, "port", MAIL_PORT)
print("Using username:", MAIL_USERNAME)

try:
    with smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=10) as s:
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(MAIL_USERNAME, MAIL_PASSWORD)
        print("✅ SMTP login: SUCCESS")
except Exception as e:
    print("❌ SMTP login: FAILED ->", repr(e))

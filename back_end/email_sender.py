# email_sender.py
import os
import smtplib
from email.message import EmailMessage
from urllib.parse import urlencode

# Config from environment (safe; do not hardcode secrets in production)
FRONTEND_RESET_URL = os.environ.get("FRONTEND_RESET_URL", "http://localhost:3000/reset-password")
MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
MAIL_USERNAME = os.environ.get("MAIL_USERNAME")  # must be set in env
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")  # must be set in env
MAIL_FROM = os.environ.get("MAIL_FROM", MAIL_USERNAME or "noreply@codewatch.local")
USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() in ("1", "true", "yes")


def _build_message(recipient_email: str, token: str) -> EmailMessage:
    """Builds the reset password email message."""
    params = urlencode({"token": token})
    reset_link = f"{FRONTEND_RESET_URL}?{params}"
    subject = "CodeWatch — Reset your password"
    body = (
        f"Hi,\n\n"
        f"You (or someone using this email) requested a password reset for CodeWatch.\n\n"
        f"Click the link below to reset your password (valid for a short time):\n\n"
        f"{reset_link}\n\n"
        "If you did not request this, ignore this email.\n\n— CodeWatch"
    )
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = MAIL_FROM
    msg["To"] = recipient_email
    msg.set_content(body)
    return msg


def send_reset_email_smtp(recipient_email: str, token: str, timeout: int = 15) -> bool:
    """Send reset email. Returns True on success, False on failure."""
    if not MAIL_USERNAME or not MAIL_PASSWORD:
        print("[email_sender] ❌ ERROR: MAIL_USERNAME or MAIL_PASSWORD are not set.")
        return False

    msg = _build_message(recipient_email, token)

    try:
        if USE_SSL:
            # Implicit SSL (usually port 465)
            with smtplib.SMTP_SSL(MAIL_SERVER, MAIL_PORT, timeout=timeout) as smtp:
                smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
                smtp.send_message(msg)
        else:
            # STARTTLS (usually port 587)
            with smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=timeout) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.ehlo()
                smtp.login(MAIL_USERNAME, MAIL_PASSWORD)
                smtp.send_message(msg)

        print(f"[email_sender] ✅ Sent reset email to {recipient_email}")
        return True

    except Exception as e:
        print(f"[email_sender] ❌ Failed to send email to {recipient_email}: {e}")
        return False


def send_test_mail(to_addr: str = None):
    """Helper for testing email sending manually."""
    to = to_addr or MAIL_USERNAME
    token = "test-token-12345"
    ok = send_reset_email_smtp(to, token)
    print("send_test_mail:", "OK" if ok else "FAILED")
    return ok

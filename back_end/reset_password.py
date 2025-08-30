# reset_password.py
import os
import time
import secrets
import logging
from urllib.parse import urlencode
from typing import Optional
from database import get_conn
from email_sender import send_reset_email_smtp

LOG = logging.getLogger("reset_password")
logging.basicConfig(level=logging.INFO)

TOKEN_BYTES = 24
TOKEN_TTL_SECONDS = 15 * 60  # 15 minutes

FRONTEND_RESET_URL = os.environ.get(
    "FRONTEND_RESET_URL",
    "http://localhost:3000/reset-password"  # change if your frontend runs elsewhere
)

def create_reset_token(email: str) -> Optional[str]:
    """Create a token for `email`, store it, and send a reset email."""
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE email = ?", (email.lower(),))
            if not cur.fetchone():
                LOG.info("create_reset_token: email not found: %s", email)
                return None

            token = secrets.token_urlsafe(TOKEN_BYTES)
            expires = int(time.time()) + TOKEN_TTL_SECONDS
            conn.execute(
                "UPDATE users SET reset_token = ?, reset_expires = ? WHERE email = ?",
                (token, expires, email.lower())
            )
            conn.commit()

        LOG.info("create_reset_token: token created for %s (expires %d)", email, expires)

        # Send reset email via SMTP
        if not send_reset_email_smtp(email, token):
            LOG.warning("create_reset_token: failed to send reset email to %s", email)
            return None

        return token
    except Exception as e:
        LOG.exception("create_reset_token: unexpected error for %s: %s", email, e)
        return None

def validate_reset_token(token: str) -> Optional[str]:
    """Return the associated email if token exists and not expired, else None."""
    try:
        now = int(time.time())
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT email FROM users WHERE reset_token = ? AND reset_expires >= ?",
                (token, now)
            )
            row = cur.fetchone()

        if row:
            try:
                return row["email"]
            except Exception:
                return row[0]
        return None
    except Exception as e:
        LOG.exception("validate_reset_token: error validating token: %s", e)
        return None

def clear_reset_token(email: str) -> None:
    """Clear token fields for the given email."""
    try:
        with get_conn() as conn:
            conn.execute(
                "UPDATE users SET reset_token = NULL, reset_expires = NULL WHERE email = ?",
                (email.lower(),)
            )
            conn.commit()
        LOG.info("clear_reset_token: cleared token for %s", email)
    except Exception as e:
        LOG.exception("clear_reset_token: error clearing token for %s: %s", email, e)

# Optional: keep for debugging only
def send_reset_email_console(email: str, token: str) -> None:
    """Print a clickable reset link to the server console (for development)."""
    try:
        params = urlencode({"token": token})
        link = f"{FRONTEND_RESET_URL}?{params}"
        LOG.info("[CodeWatch] Reset link for %s: %s", email, link)
        print(f"[CodeWatch] Reset link for {email}: {link}")
    except Exception as e:
        LOG.exception("send_reset_email_console: error building link for %s: %s", email, e)

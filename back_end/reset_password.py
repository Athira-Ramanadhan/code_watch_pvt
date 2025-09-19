# reset_password.py
import os
import time
import secrets
import logging
from urllib.parse import urlencode
from typing import Optional
from database import safe_execute, clear_reset_token_by_token, clear_reset_token_by_email
from email_sender import send_reset_email_smtp

LOG = logging.getLogger("reset_password")
logging.basicConfig(level=logging.INFO)

TOKEN_BYTES = 24
TOKEN_TTL_SECONDS = 15 * 60  # 15 minutes

FRONTEND_RESET_URL = os.environ.get(
    "FRONTEND_RESET_URL",
    "http://localhost:3000/reset-password"  # change if your frontend runs elsewhere
)


# ----------------- Create Reset Token -----------------
def create_reset_token(email: str) -> Optional[str]:
    """Create a token for `email`, store it, and send a reset email."""
    try:
        # Check if email exists
        cur = safe_execute(
            "SELECT id FROM users WHERE email = ?",
            (email.lower(),),
            commit=False
        )
        if not cur.fetchone():
            LOG.info("create_reset_token: email not found: %s", email)
            return None

        # Generate token + expiry
        token = secrets.token_urlsafe(TOKEN_BYTES)
        expires = int(time.time()) + TOKEN_TTL_SECONDS

        safe_execute(
            "UPDATE users SET reset_token = ?, reset_expires = ? WHERE email = ?",
            (token, expires, email.lower())
        )

        LOG.info("create_reset_token: token created for %s (expires %d)", email, expires)

        # Send reset email via SMTP
        if not send_reset_email_smtp(email, token):
            LOG.warning("create_reset_token: failed to send reset email to %s", email)
            return None

        return token
    except Exception as e:
        LOG.exception("create_reset_token: unexpected error for %s: %s", email, e)
        return None


# ----------------- Validate Token -----------------
def validate_reset_token(token: str) -> Optional[str]:
    """Return the associated email if token exists and not expired, else None.
       If expired, automatically clear it."""
    try:
        now = int(time.time())
        cur = safe_execute(
            "SELECT email, reset_expires FROM users WHERE reset_token = ?",
            (token,),
            commit=False
        )
        row = cur.fetchone()

        if not row:
            return None

        email = row["email"] if "email" in row.keys() else row[0]
        expires = row["reset_expires"] if "reset_expires" in row.keys() else row[1]

        if expires and expires >= now:
            return email

        # ❌ expired — clear it
        clear_reset_token_by_token(token)
        LOG.info("validate_reset_token: expired token cleared for %s", email)
        return None
    except Exception as e:
        LOG.exception("validate_reset_token: error validating token: %s", e)
        return None


# ----------------- Clear Token -----------------
def clear_reset_token(email: str) -> None:
    """Clear token fields for the given email after successful reset."""
    try:
        clear_reset_token_by_email(email)
        LOG.info("clear_reset_token: cleared token for %s", email)
    except Exception as e:
        LOG.exception("clear_reset_token: error clearing token for %s: %s", email, e)


# ----------------- Debug Helper -----------------
def send_reset_email_console(email: str, token: str) -> None:
    """Print a clickable reset link to the server console (for development)."""
    try:
        params = urlencode({"token": token})
        link = f"{FRONTEND_RESET_URL}?{params}"
        LOG.info("[CodeWatch] Reset link for %s: %s", email, link)
        print(f"[CodeWatch] Reset link for {email}: {link}")
    except Exception as e:
        LOG.exception("send_reset_email_console: error building link for %s: %s", email, e)

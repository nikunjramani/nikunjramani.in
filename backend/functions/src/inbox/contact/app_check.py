"""Firebase App Check verification — only the contact form uses it (ADR 0020).

The browser attests with reCAPTCHA Enterprise and sends the resulting App Check token in the
X-Firebase-AppCheck header. Verifying it needs no secret: the Admin SDK checks the token's
signature against Google's public keys and its audience against this project.
"""

from __future__ import annotations

from firebase_admin import app_check

from kernel.config import get_settings
from kernel.firebase import ensure_app
from kernel.logging import get_logger

log = get_logger(__name__)

HEADER = "X-Firebase-AppCheck"


def verify_app_check(token: str) -> bool:
    """True if the token is valid. Fails closed on any error — an App Check outage should not
    turn into an open contact form. Only local development (emulators, no reCAPTCHA key)
    runs without one."""
    if not get_settings().is_production:
        if not token:
            log.warning("no App Check token — skipping verification (dev mode)")
            return True
    elif not token:
        return False

    try:
        app_check.verify_token(token, app=ensure_app())
    except Exception as exc:  # invalid, expired, wrong project, or JWKS fetch failure
        log.warning("App Check verification failed", extra={"extra_fields": {"error": str(exc)}})
        return False
    return True

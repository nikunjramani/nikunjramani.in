"""Cloudflare Turnstile server-side verification.

Contact-specific rather than shared/: nothing else in this project uses Turnstile, and
sharing code that only one domain calls just adds an indirection with no payoff.
"""

from __future__ import annotations

import httpx

from shared.core.config import get_settings
from shared.core.logging import get_logger

log = get_logger(__name__)

_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def verify_turnstile(token: str, *, remote_ip: str) -> bool:
    """True if the token is valid. Fails closed on any error — a Turnstile outage should
    not turn into an open contact form."""
    settings = get_settings()

    if not settings.turnstile_secret_key:
        # Local development without a site configured yet (Turnstile setup is a Phase 3
        # prerequisite not yet done — billing/external services are deferred). Passing
        # here lets the rest of the flow be exercised against the emulator today.
        log.warning("TURNSTILE_SECRET_KEY not set — skipping verification (dev mode)")
        return True

    if not token:
        return False

    try:
        response = httpx.post(
            _VERIFY_URL,
            data={
                "secret": settings.turnstile_secret_key,
                "response": token,
                "remoteip": remote_ip,
            },
            timeout=5.0,
        )
        response.raise_for_status()
        return bool(response.json().get("success", False))
    except httpx.HTTPError as exc:
        log.warning(
            "turnstile verification request failed", extra={"extra_fields": {"error": str(exc)}}
        )
        return False

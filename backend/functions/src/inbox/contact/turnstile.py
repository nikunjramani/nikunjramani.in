"""Cloudflare Turnstile server-side verification — only the contact form uses it."""

from __future__ import annotations

import httpx

from kernel.config import get_settings
from kernel.logging import get_logger
from src.inbox.contact.settings import get_contact_settings

log = get_logger(__name__)

_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def verify_turnstile(token: str, *, remote_ip: str) -> bool:
    """True if the token is valid. Fails closed on any error — a Turnstile outage should
    not turn into an open contact form. Only local development may run without a key."""
    secret = get_contact_settings().turnstile_secret_key

    if not secret:
        if get_settings().is_production:
            log.error("TURNSTILE_SECRET_KEY not set in production — rejecting submission")
            return False
        log.warning("TURNSTILE_SECRET_KEY not set — skipping verification (dev mode)")
        return True

    if not token:
        return False

    try:
        response = httpx.post(
            _VERIFY_URL,
            data={
                "secret": secret,
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

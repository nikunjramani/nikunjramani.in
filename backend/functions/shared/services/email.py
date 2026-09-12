"""Resend wrapper, with a retry. See docs/plan/03-security.md."""

from __future__ import annotations

import httpx

from shared.core.config import get_settings
from shared.core.errors import DomainError
from shared.core.logging import get_logger

log = get_logger(__name__)

_RESEND_API = "https://api.resend.com/emails"


class EmailDeliveryError(DomainError):
    status_code = 502
    code = "email_delivery_failed"


def send_email(*, to: str, subject: str, html: str, retries: int = 2) -> None:
    settings = get_settings()

    if not settings.resend_api_key:
        # Local development without a key configured: log instead of failing loudly,
        # so the rest of the flow (rate limiting, spam scoring, the Firestore write) can
        # still be exercised against the emulator without a real Resend account.
        log.warning(
            "RESEND_API_KEY not set — skipping send",
            extra={"extra_fields": {"to": to, "subject": subject}},
        )
        return

    headers = {"Authorization": f"Bearer {settings.resend_api_key}"}
    payload = {"from": settings.mail_from, "to": [to], "subject": subject, "html": html}

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            response = httpx.post(_RESEND_API, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            return
        except httpx.HTTPError as exc:
            last_error = exc
            log.warning(
                "email send attempt failed",
                extra={"extra_fields": {"attempt": attempt, "error": str(exc)}},
            )

    raise EmailDeliveryError("Failed to send email after retries.") from last_error

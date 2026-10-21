"""Resend wrapper, with a retry. See .docs/plan/03-security.md.

Failures split by whether trying again could help. A network error, a 5xx or a 429 raises
EmailDeliveryError: the event handler answers 5xx and Eventarc redelivers later. Any other
4xx — a bad key, an unverified sender, a rejected payload — is logged and dropped: it would
fail the same way on every one of a day's redeliveries, and the message itself is already
stored and visible in the admin inbox."""

from __future__ import annotations

import httpx

from kernel.errors import DomainError
from kernel.logging import get_logger
from src.inbox.notifications.settings import get_notification_settings

log = get_logger(__name__)

_RESEND_API = "https://api.resend.com/emails"


class EmailDeliveryError(DomainError):
    status_code = 502
    code = "email_delivery_failed"


def send_email(*, to: str, subject: str, html: str, retries: int = 2) -> None:
    settings = get_notification_settings()

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
            if _rejected_for_good(response.status_code):
                log.error(
                    "email rejected by Resend — not retrying",
                    extra={"extra_fields": {"status": response.status_code}},
                )
                return
            response.raise_for_status()
            return
        except httpx.HTTPError as exc:
            last_error = exc
            log.warning(
                "email send attempt failed",
                extra={"extra_fields": {"attempt": attempt, "error": str(exc)}},
            )

    raise EmailDeliveryError("Failed to send email after retries.") from last_error


def _rejected_for_good(status: int) -> bool:
    """A 4xx other than 429 (rate limited) won't change on a retry."""
    return 400 <= status < 500 and status != 429

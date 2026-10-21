"""Resend wrapper. See .docs/plan/03-security.md.

One attempt per delivery: retrying is Eventarc's job (it redelivers a failed event with
backoff, for up to a day), and the idempotency key keeps a redelivery from sending twice —
Resend remembers a key for 24 hours, the same window Eventarc retries in.

Failures split by whether trying again could help. A network error, a 5xx, a 429 or a 409
(Resend still processing the same key) raises EmailDeliveryError: the event handler answers
5xx and Eventarc redelivers later. Any other 4xx — a bad key, an unverified sender, a
rejected payload — is logged and dropped: it would fail the same way on every redelivery,
and the message itself is already stored and visible in the admin inbox."""

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


def send_email(*, to: str, subject: str, html: str, idempotency_key: str) -> None:
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

    headers = {
        "Authorization": f"Bearer {settings.resend_api_key}",
        "Idempotency-Key": idempotency_key,
    }
    payload = {"from": settings.mail_from, "to": [to], "subject": subject, "html": html}

    try:
        response = httpx.post(_RESEND_API, headers=headers, json=payload, timeout=10.0)
    except httpx.HTTPError as exc:
        raise EmailDeliveryError("Could not reach Resend.") from exc
    if _rejected_for_good(response.status_code):
        log.error(
            "email rejected by Resend — not retrying",
            extra={"extra_fields": {"status": response.status_code}},
        )
        return
    if response.is_error:
        raise EmailDeliveryError(f"Resend answered {response.status_code}.")


def _rejected_for_good(status: int) -> bool:
    """A 4xx won't change on a retry — except 429 (rate limited) and 409 (Resend is still
    handling an earlier request with the same idempotency key)."""
    return 400 <= status < 500 and status not in (409, 429)

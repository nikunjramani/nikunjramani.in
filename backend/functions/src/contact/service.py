"""Contact form business rules.

Every anti-abuse check here fails *silently* — the caller always sees success. This is a
deliberate trade documented in docs/plan/03-security.md: telling a bot which check it hit
only helps it get past the next one. The cost is that a genuine sender who trips a false
positive (a shared office IP that used up its rate-limit window, say) will not be told why
their message did not arrive. That trade only makes sense because this is a low-volume
personal contact form, not a support channel someone depends on.

Field-level problems (missing name, message too long) are the one case that stays honest —
those are FastAPI/Pydantic validation errors on the request body, raised before this
service ever runs, and a real visitor benefits from being told to fix them.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from google.cloud.firestore_v1 import Client

from shared.core.errors import RateLimitedError
from shared.core.rate_limit import RateLimiter
from shared.core.timestamps import now_iso
from shared.generated import ContactMessage
from src.contact.repository import ContactRepository
from src.contact.spam import score_spam
from src.contact.turnstile import verify_turnstile

_RETENTION = timedelta(days=730)  # 2 years — matches the schema's TTL field and the ADR


class ContactService:
    def __init__(self, db: Client | None = None) -> None:
        self._repo = ContactRepository(db)
        self._limiter = RateLimiter(db)

    def submit(
        self,
        *,
        name: str,
        email: str,
        message: str,
        ip: str,
        user_agent: str,
        subject: str | None = None,
        honeypot: str = "",
        turnstile_token: str = "",
    ) -> None:
        if honeypot:
            return  # a real visitor never fills this field; a bot's form-filler always does

        try:
            self._limiter.check(scope="contact_ip", identifier=ip, limit=3, window_seconds=3600)
            self._limiter.check(
                scope="contact_global", identifier="all", limit=20, window_seconds=3600
            )
        except RateLimitedError:
            return

        if not verify_turnstile(turnstile_token, remote_ip=ip):
            return

        now = datetime.now(UTC)
        entry = ContactMessage(
            name=name,
            email=email,
            subject=subject,
            message=message,
            ip=ip,
            userAgent=user_agent,
            spamScore=score_spam(message),
            read=False,
            replied=False,
            createdAt=now_iso(),  # type: ignore[arg-type]
            expiresAt=(now + _RETENTION).isoformat(),  # type: ignore[arg-type]
        )
        self._repo.create(entry)

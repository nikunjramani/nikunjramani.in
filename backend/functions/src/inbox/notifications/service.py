"""Owner notification for a new contact message. The API's job is to persist a validated
message quickly; emailing it happens here, off the request path, in the trigger."""

from __future__ import annotations

from html import escape
from typing import Any

from kernel.logging import get_logger
from src.inbox.notifications.email import send_email
from src.inbox.notifications.settings import get_notification_settings

log = get_logger(__name__)


def render_email(data: dict[str, Any]) -> tuple[str, str]:
    """(subject, html) for one message. Every visitor-supplied value is escaped — the body
    is untrusted public input landing in the owner's inbox."""
    name = " ".join(str(data.get("name") or "someone").split())
    subject = f"nikunjramani.in — message from {name}"

    def field(key: str, fallback: str = "") -> str:
        return escape(str(data.get(key) or fallback))

    spam_note = ""
    score = data.get("spamScore")
    if isinstance(score, int | float) and score >= 0.5:
        spam_note = f"<p><b>⚠ Spam score: {score:.2f}</b></p>"

    message = field("message").replace("\n", "<br>")
    html = (
        f"{spam_note}"
        f"<p><b>From:</b> {field('name')} &lt;{field('email')}&gt;</p>"
        f"<p><b>Subject:</b> {field('subject', '(none)')}</p>"
        f"<p>{message}</p>"
    )
    return subject, html


def notify_owner(data: dict[str, Any]) -> None:
    to = get_notification_settings().contact_email_to
    if not to:
        log.warning("CONTACT_EMAIL_TO not set — cannot forward this message")
        return
    subject, html = render_email(data)
    send_email(to=to, subject=subject, html=html)

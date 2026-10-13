"""on_contact_created — fires when a message lands in Firestore, and emails it to the
owner. Separate from the write path itself: the API's job is to persist a validated
message quickly, not to wait on an outbound email request."""

from __future__ import annotations

from html import escape
from typing import Any

from firebase_functions import firestore_fn
from google.cloud.firestore_v1 import DocumentSnapshot

from shared.core.config import get_settings
from shared.core.logging import get_logger
from shared.services.email import send_email

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


@firestore_fn.on_document_created(
    document="contact_messages/{message_id}",
    region="asia-south1",
    secrets=["CONTACT_EMAIL_TO", "RESEND_API_KEY"],
)
def on_contact_created(event: firestore_fn.Event[DocumentSnapshot | None]) -> None:
    settings = get_settings()
    if not settings.contact_email_to:
        log.warning("CONTACT_EMAIL_TO not set — cannot forward this message")
        return

    snapshot = event.data
    if snapshot is None:
        return

    subject, html = render_email(snapshot.to_dict() or {})
    send_email(to=settings.contact_email_to, subject=subject, html=html)

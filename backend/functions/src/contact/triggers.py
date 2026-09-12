"""on_contact_created — fires when a message lands in Firestore, and emails it to the
owner. Separate from the write path itself: the API's job is to persist a validated
message quickly, not to wait on an outbound email request."""

from __future__ import annotations

from firebase_functions import firestore_fn
from google.cloud.firestore_v1 import DocumentSnapshot

from shared.core.config import get_settings
from shared.core.logging import get_logger
from shared.services.email import send_email

log = get_logger(__name__)


@firestore_fn.on_document_created(document="contact_messages/{message_id}", region="asia-south1")
def on_contact_created(event: firestore_fn.Event[DocumentSnapshot | None]) -> None:
    settings = get_settings()
    if not settings.contact_email_to:
        log.warning("CONTACT_EMAIL_TO not set — cannot forward this message")
        return

    snapshot = event.data
    if snapshot is None:
        return
    data = snapshot.to_dict() or {}

    spam_note = ""
    if isinstance(data.get("spamScore"), int | float) and data["spamScore"] >= 0.5:
        spam_note = f"<p><b>⚠ Spam score: {data['spamScore']:.2f}</b></p>"

    send_email(
        to=settings.contact_email_to,
        subject=f"nikunjramani.in — message from {data.get('name', 'someone')}",
        html=(
            f"{spam_note}"
            f"<p><b>From:</b> {data.get('name')} &lt;{data.get('email')}&gt;</p>"
            f"<p><b>Subject:</b> {data.get('subject') or '(none)'}</p>"
            f"<p>{data.get('message', '')}</p>"
        ),
    )

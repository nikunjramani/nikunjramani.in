"""inbox/notifications — entry point: deploys on_contact_created (Firestore trigger).

CONTACT_EMAIL_TO and RESEND_API_KEY must have Secret Manager versions before deploy."""

from firebase_functions import firestore_fn
from google.cloud.firestore_v1 import DocumentSnapshot

from src.inbox.notifications.service import notify_owner


@firestore_fn.on_document_created(
    document="contact_messages/{message_id}",
    region="asia-south1",
    secrets=["CONTACT_EMAIL_TO", "RESEND_API_KEY"],
)
def on_contact_created(event: firestore_fn.Event[DocumentSnapshot | None]) -> None:
    if event.data is not None:
        notify_owner(event.data.to_dict() or {})

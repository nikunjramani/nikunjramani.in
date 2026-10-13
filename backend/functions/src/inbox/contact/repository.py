"""contact_messages — what the contact form needs: store a new message. Reading and triage
belong to inbox/messages, which has its own repository for that."""

from __future__ import annotations

from google.cloud.firestore_v1 import Client

from kernel.firebase import get_db
from kernel.timestamps import to_firestore
from shared.generated import ContactMessage


class NewMessageRepository:
    collection = "contact_messages"

    def __init__(self, db: Client | None = None) -> None:
        self._db = db if db is not None else get_db()

    @property
    def db(self) -> Client:
        return self._db

    def create(self, message: ContactMessage) -> str:
        ref = self._db.collection(self.collection).document()
        ref.set(to_firestore(message.model_dump(mode="json", exclude_none=True)))
        return str(ref.id)

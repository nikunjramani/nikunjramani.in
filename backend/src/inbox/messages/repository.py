"""contact_messages — what the admin inbox needs: read, mark, delete. (New messages are
stored by inbox/contact, through its own repository.)"""

from __future__ import annotations

from google.cloud.firestore_v1 import Client, CollectionReference

from kernel.errors import NotFoundError
from kernel.firebase import get_db
from kernel.records import Record
from kernel.timestamps import from_firestore, to_firestore
from shared.generated import ContactMessage

COLLECTION = "contact_messages"


class MessageRepository:
    collection = COLLECTION

    def __init__(self, db: Client | None = None) -> None:
        self._db = db if db is not None else get_db()

    @property
    def db(self) -> Client:
        return self._db

    @property
    def _ref(self) -> CollectionReference:
        return self._db.collection(self.collection)

    def get(self, doc_id: str) -> Record[ContactMessage] | None:
        snap = self._ref.document(doc_id).get()
        return self._record(doc_id, snap.to_dict() or {}) if snap.exists else None

    def require(self, doc_id: str) -> Record[ContactMessage]:
        record = self.get(doc_id)
        if record is None:
            raise NotFoundError(f"Message '{doc_id}' not found.")
        return record

    def list_all(self) -> list[Record[ContactMessage]]:
        """Unordered on purpose: Firestore's order_by silently drops documents missing the
        field, and an inbox must never lose a message. Callers sort null-safely."""
        return [self._record(s.id, s.to_dict() or {}) for s in self._ref.stream()]

    def update(self, doc_id: str, fields: dict[str, object]) -> Record[ContactMessage]:
        self.require(doc_id)  # 404 rather than silently creating
        self._ref.document(doc_id).update(to_firestore(dict(fields)))
        return self.require(doc_id)

    def delete(self, doc_id: str) -> None:
        self.require(doc_id)
        self._ref.document(doc_id).delete()

    @staticmethod
    def _record(doc_id: str, raw: dict[str, object]) -> Record[ContactMessage]:
        return Record(id=doc_id, data=ContactMessage.model_validate(from_firestore(raw)))

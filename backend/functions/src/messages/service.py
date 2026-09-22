"""Admin-side view over contact_messages. `contact` owns creation (POST /contact, with its
anti-abuse checks) — this domain only ever reads and updates, never creates. Doesn't fit
shared/crud.py: no visibility/publish concept, and "mark read/replied" is a narrower
operation than a general merge-patch."""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime

from google.cloud.firestore_v1 import Client

from shared.generated import ContactMessage
from shared.repositories.base import Record
from src.messages.repository import MessageRepository


class MessageService:
    def __init__(self, db: Client | None = None, *, repo: MessageRepository | None = None) -> None:
        self.repo = repo if repo is not None else MessageRepository(db)

    def list_all(self, *, unread_only: bool = False) -> list[Record[ContactMessage]]:
        # order_by=None + a client-side sort: Firestore's server-side .order_by("createdAt")
        # would silently drop any message missing that field, which is a worse failure for
        # an inbox than one that sorts slightly wrong. See BaseRepository.list_all.
        messages = self._sorted(self.repo.list_all(order_by=None))
        if unread_only:
            messages = [m for m in messages if not m.data.read]
        return messages

    @staticmethod
    def _sorted(messages: list[Record[ContactMessage]]) -> list[Record[ContactMessage]]:
        # createdAt is an AwareDatetime | None — "or ''" would crash comparing a real
        # timestamp against a string the one time a message actually lacks one, which is
        # exactly the case this sort needs to handle without blowing up.
        return sorted(
            messages,
            key=lambda m: m.data.createdAt or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )

    def get(self, doc_id: str) -> Record[ContactMessage]:
        return self.repo.require(doc_id)

    def mark_read(self, doc_id: str, *, read: bool = True) -> Record[ContactMessage]:
        return self.repo.update(doc_id, {"read": read})

    def mark_replied(self, doc_id: str, *, replied: bool = True) -> Record[ContactMessage]:
        return self.repo.update(doc_id, {"replied": replied})

    def delete(self, doc_id: str) -> None:
        self.repo.delete(doc_id)

    def export_csv(self) -> str:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            ["name", "email", "subject", "message", "createdAt", "read", "replied", "spamScore"]
        )
        for record in self._sorted(self.repo.list_all(order_by=None)):
            m = record.data
            writer.writerow(
                [
                    m.name,
                    m.email,
                    m.subject or "",
                    m.message,
                    m.createdAt,
                    m.read,
                    m.replied,
                    m.spamScore,
                ]
            )
        return buffer.getvalue()

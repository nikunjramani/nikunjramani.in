"""Admin-side view over contact_messages. `contact` owns creation (POST /contact, with its
anti-abuse checks) — this domain only ever reads and updates, never creates. Doesn't fit
shared/crud.py: no visibility/publish concept, and "mark read/replied" is a narrower
operation than a general merge-patch."""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime
from typing import Any

from google.cloud.firestore_v1 import Client

from shared.crud import actor_of
from shared.generated import ContactMessage
from shared.repositories.base import Record
from shared.services.audit import Action, AuditService
from src.messages.repository import MessageRepository

# A cell starting with one of these is a formula to Excel/Sheets — and every text column
# here comes from the public contact form.
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def csv_safe(value: object) -> object:
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


class MessageService:
    def __init__(
        self,
        db: Client | None = None,
        *,
        repo: MessageRepository | None = None,
        audit: AuditService | None = None,
    ) -> None:
        self.repo = repo if repo is not None else MessageRepository(db)
        self._audit = audit if audit is not None else AuditService(self.repo.db)

    def list_all(self, *, unread_only: bool = False) -> list[Record[ContactMessage]]:
        # order_by=None + a client-side sort: Firestore's server-side .order_by("createdAt")
        # would silently drop any message missing that field. See BaseRepository.list_all.
        messages = self._sorted(self.repo.list_all(order_by=None))
        if unread_only:
            messages = [m for m in messages if not m.data.read]
        return messages

    @staticmethod
    def _sorted(messages: list[Record[ContactMessage]]) -> list[Record[ContactMessage]]:
        return sorted(
            messages,
            key=lambda m: m.data.createdAt or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )

    def get(self, doc_id: str) -> Record[ContactMessage]:
        return self.repo.require(doc_id)

    def mark_read(
        self, doc_id: str, claims: dict[str, object], *, read: bool = True
    ) -> Record[ContactMessage]:
        return self._update(doc_id, {"read": read}, claims)

    def mark_replied(
        self, doc_id: str, claims: dict[str, object], *, replied: bool = True
    ) -> Record[ContactMessage]:
        return self._update(doc_id, {"replied": replied}, claims)

    def delete(self, doc_id: str, claims: dict[str, object]) -> None:
        before = self.repo.require(doc_id)
        self.repo.delete(doc_id)
        self._record("delete", doc_id, claims, before=_dump(before), after=None)

    def export_csv(self) -> str:
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            ["name", "email", "subject", "message", "createdAt", "read", "replied", "spamScore"]
        )
        for record in self._sorted(self.repo.list_all(order_by=None)):
            m = record.data
            row = [m.name, m.email, m.subject or "", m.message, m.createdAt]
            writer.writerow([*map(csv_safe, row), m.read, m.replied, m.spamScore])
        return buffer.getvalue()

    def _update(
        self, doc_id: str, fields: dict[str, object], claims: dict[str, object]
    ) -> Record[ContactMessage]:
        before = self.repo.require(doc_id)
        record = self.repo.update(doc_id, fields)
        self._record("update", doc_id, claims, before=_dump(before), after=_dump(record))
        return record

    def _record(
        self,
        action: Action,
        doc_id: str,
        claims: dict[str, object],
        *,
        before: dict[str, Any] | None,
        after: dict[str, Any] | None,
    ) -> None:
        uid, email = actor_of(claims)
        self._audit.record(
            actor=uid,
            actor_email=email,
            action=action,
            collection=self.repo.collection,
            doc_id=doc_id,
            before=before,
            after=after,
        )


def _dump(record: Record[ContactMessage]) -> dict[str, Any]:
    return record.data.model_dump(mode="json", exclude_none=True)

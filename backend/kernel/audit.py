"""The audit trail. Every admin mutation, in every domain, records one entry in audit_log;
ops/audit reads them back. Infrastructure, like logging — it knows the audit-log shape
(shared.generated.AuditLog), never any domain's data.

A service builds the entry (`AuditEntry`); the repository writes it in the *same batch* as
the change it describes (`stage`), so a change can't land without its entry or an entry
without its change. Only identity/admins, whose change is in Firebase Auth rather than
Firestore, writes an entry on its own (`AuditWriter`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from google.cloud.firestore_v1 import Client, WriteBatch

from kernel.firebase import get_db
from kernel.security import Actor
from kernel.timestamps import now_iso, to_firestore
from shared.generated import AuditLog

COLLECTION = "audit_log"

Action = Literal["create", "update", "delete", "publish", "unpublish", "reorder"]


@dataclass(frozen=True, slots=True)
class AuditEntry:
    actor: Actor
    action: Action
    collection: str
    doc_id: str | None
    before: dict[str, Any] | None
    after: dict[str, Any] | None

    def payload(self) -> dict[str, Any]:
        entry = AuditLog(
            actor=self.actor.uid,
            actorEmail=self.actor.email,
            action=self.action,  # type: ignore[arg-type]
            collection=self.collection,
            docId=self.doc_id,
            before=self.before,
            after=self.after,
            at=now_iso(),  # type: ignore[arg-type]
        )
        # No exclude_none: a create has no `before`, a delete no `after`; an explicit null
        # reads differently from a missing key to anyone inspecting the trail.
        return to_firestore(entry.model_dump(mode="json"))


def stage(db: Client, batch: WriteBatch, entry: AuditEntry | None) -> None:
    """Add `entry` to a repository's write batch (a no-op for None)."""
    if entry is not None:
        batch.set(db.collection(COLLECTION).document(), entry.payload())


class AuditWriter:
    """Writes an entry on its own — for a change made outside Firestore (Firebase Auth)."""

    def __init__(self, db: Client | None = None) -> None:
        self._db = db if db is not None else get_db()

    def record(self, entry: AuditEntry) -> None:
        self._db.collection(COLLECTION).document().set(entry.payload())

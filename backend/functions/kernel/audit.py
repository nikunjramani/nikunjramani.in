"""The audit trail writer. Every admin mutation, in every domain, records one entry in
audit_log; ops/audit reads them back. Infrastructure, like logging — it knows the audit-log
shape (shared.generated.AuditLog), never any domain's data."""

from __future__ import annotations

from typing import Any, Literal

from google.cloud.firestore_v1 import Client

from kernel.firebase import get_db
from kernel.security import actor_of
from kernel.timestamps import now_iso, to_firestore
from shared.generated import AuditLog

Action = Literal["create", "update", "delete", "publish", "unpublish", "reorder"]


class AuditWriter:
    def __init__(self, db: Client | None = None) -> None:
        self._db = db if db is not None else get_db()

    def record(
        self,
        *,
        claims: dict[str, object],
        action: Action,
        collection: str,
        doc_id: str | None,
        before: dict[str, Any] | None,
        after: dict[str, Any] | None,
    ) -> None:
        uid, email = actor_of(claims)
        entry = AuditLog(
            actor=uid,
            actorEmail=email,
            action=action,  # type: ignore[arg-type]
            collection=collection,
            docId=doc_id,
            before=before,
            after=after,
            at=now_iso(),  # type: ignore[arg-type]
        )
        # No exclude_none: a create has no `before`, a delete no `after`; an explicit null
        # reads differently from a missing key to anyone inspecting the trail.
        self._db.collection("audit_log").document().set(to_firestore(entry.model_dump(mode="json")))

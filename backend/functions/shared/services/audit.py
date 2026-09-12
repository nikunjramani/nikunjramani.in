"""Every admin mutation writes one of these. Never client-readable — see ADR 0007."""

from __future__ import annotations

from typing import Any, Literal

from google.cloud.firestore_v1 import Client

from shared.core.firebase import get_db
from shared.core.timestamps import now_iso, to_firestore
from shared.generated import AuditLog

Action = Literal["create", "update", "delete", "publish", "unpublish", "reorder"]


class AuditService:
    def __init__(self, db: Client | None = None) -> None:
        self._db = db if db is not None else get_db()

    def record(
        self,
        *,
        actor: str,
        action: Action,
        collection: str,
        doc_id: str | None = None,
        actor_email: str | None = None,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
    ) -> None:
        entry = AuditLog(
            actor=actor,
            actorEmail=actor_email,
            action=action,  # type: ignore[arg-type]
            collection=collection,
            docId=doc_id,
            before=before,
            after=after,
            at=now_iso(),  # type: ignore[arg-type]
        )
        payload = to_firestore(entry.model_dump(mode="json", exclude_none=True))
        self._db.collection("audit_log").document().set(payload)

"""audit_log, read side. Content, media, inbox and identity each write it through their own
writer; the audit-log schema is the contract between them, not shared code."""

from __future__ import annotations

from typing import Any

from google.cloud.firestore_v1 import Client, CollectionReference, Query
from google.cloud.firestore_v1.base_query import FieldFilter

from kernel.firebase import get_db
from kernel.timestamps import from_firestore

COLLECTION = "audit_log"


class AuditLogRepository:
    def __init__(self, db: Client | None = None) -> None:
        self._db = db if db is not None else get_db()

    def list_recent(
        self, *, collection: str | None = None, doc_id: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Newest first. Each filter combination needs its composite index (descending on
        `at`) — declared in audit-log.schema.json's x-firestore.indexes."""
        query: Query | CollectionReference = self._db.collection(COLLECTION)
        if collection is not None:
            query = query.where(filter=FieldFilter("collection", "==", collection))
        if doc_id is not None:
            query = query.where(filter=FieldFilter("docId", "==", doc_id))
        query = query.order_by("at", direction=Query.DESCENDING).limit(limit)
        return [{"id": snap.id, **from_firestore(snap.to_dict() or {})} for snap in query.stream()]

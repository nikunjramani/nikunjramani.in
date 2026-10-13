"""audit_log access. Kept apart from BaseRepository: entries are append-only, have no
id-addressed reads, and are queried newest-first by collection/document."""

from __future__ import annotations

from typing import Any

from google.cloud.firestore_v1 import Client, CollectionReference, Query
from google.cloud.firestore_v1.base_query import FieldFilter

from shared.core.firebase import get_db
from shared.core.timestamps import from_firestore, to_firestore

COLLECTION = "audit_log"


class AuditRepository:
    def __init__(self, db: Client | None = None) -> None:
        self._db = db if db is not None else get_db()

    def add(self, entry: dict[str, Any]) -> None:
        self._db.collection(COLLECTION).document().set(to_firestore(entry))

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

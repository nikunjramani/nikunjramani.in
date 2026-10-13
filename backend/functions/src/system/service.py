"""Business logic for the system domain."""

from __future__ import annotations

from typing import Any

from google.cloud.firestore_v1 import Client

from shared.repositories.audit import AuditRepository


class SystemService:
    def __init__(self, db: Client | None = None) -> None:
        self._audit = AuditRepository(db)

    def list_audit_log(
        self, *, collection: str | None = None, doc_id: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Admin-only read of the trail every mutation writes (shared/services/audit.py).
        "Never client-readable" in the schema refers to Firestore rules, not to this route."""
        return self._audit.list_recent(collection=collection, doc_id=doc_id, limit=limit)

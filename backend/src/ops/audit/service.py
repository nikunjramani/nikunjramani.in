from __future__ import annotations

from typing import Any

from src.ops.audit.repository import AuditLogRepository


class AuditService:
    def __init__(self, repo: AuditLogRepository | None = None) -> None:
        self._repo = repo if repo is not None else AuditLogRepository()

    def list_entries(
        self, *, collection: str | None = None, doc_id: str | None = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        return self._repo.list_recent(collection=collection, doc_id=doc_id, limit=limit)

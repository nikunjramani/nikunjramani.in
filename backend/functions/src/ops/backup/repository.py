"""Whole-collection reads for the export. Documents are treated as opaque JSON — this
subdomain imports no other domain's models, so it never depends on their shape."""

from __future__ import annotations

from typing import Any

from google.cloud.firestore_v1 import Client

from kernel.firebase import get_db
from kernel.timestamps import from_firestore


class CollectionDumpRepository:
    def __init__(self, db: Client | None = None) -> None:
        self._db = db if db is not None else get_db()

    def dump(self, collection: str) -> list[dict[str, Any]]:
        return [
            {"id": snap.id, "data": from_firestore(snap.to_dict() or {})}
            for snap in self._db.collection(collection).stream()
        ]

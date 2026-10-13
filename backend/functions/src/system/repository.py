"""Whole-collection reads for the nightly backup."""

from __future__ import annotations

from typing import Any

from google.cloud.firestore_v1 import Client

from shared.core.firebase import get_db
from shared.core.timestamps import from_firestore


class BackupRepository:
    def __init__(self, db: Client | None = None) -> None:
        self._db = db if db is not None else get_db()

    def dump(self, collection: str) -> list[dict[str, Any]]:
        return [
            {"id": snap.id, "data": from_firestore(snap.to_dict() or {})}
            for snap in self._db.collection(collection).stream()
        ]

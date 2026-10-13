"""Which content documents mention a given URL — the "is this image still used?" check
before a media asset is deleted. A full scan of the content collections: they hold tens
of documents, and a maintained counter would drift on every edit that adds or removes an
image (which is what the old, never-updated `usageCount` field did)."""

from __future__ import annotations

from typing import Any

from google.cloud.firestore_v1 import Client

from shared.core.collections import CONTENT_COLLECTIONS
from shared.core.firebase import get_db


class ReferenceRepository:
    def __init__(self, db: Client | None = None) -> None:
        self._db = db if db is not None else get_db()

    def documents_mentioning(
        self, needles: set[str], collections: tuple[str, ...] = CONTENT_COLLECTIONS
    ) -> list[str]:
        """`collection/id` of every document holding any of `needles` as a string value."""
        found: list[str] = []
        for collection in collections:
            for snap in self._db.collection(collection).stream():
                if _contains(snap.to_dict() or {}, needles):
                    found.append(f"{collection}/{snap.id}")
        return found


def _contains(value: Any, needles: set[str]) -> bool:
    if isinstance(value, str):
        return value in needles
    if isinstance(value, dict):
        return any(_contains(v, needles) for v in value.values())
    if isinstance(value, list):
        return any(_contains(v, needles) for v in value)
    return False

"""Nightly export of every collection as plain per-document JSON.

Not GCP's native export: a backup has to be restorable into the *emulator* to verify it
before touching production, and the native format only imports into real Firestore.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from kernel.logging import get_logger
from src.ops.backup.repository import CollectionDumpRepository
from src.ops.backup.storage import BackupStorage

log = get_logger(__name__)

# Everything worth restoring after a disaster; rate-limit windows deliberately absent.
# tests/test_domain_registry.py checks this covers every collection the schemas declare.
BACKED_UP_COLLECTIONS: tuple[str, ...] = (
    "profile",
    "projects",
    "skills",
    "experience",
    "education",
    "certifications",
    "posts",
    "site_config",
    "contact_messages",
    "media_assets",
    "audit_log",
)


class BackupService:
    def __init__(
        self,
        repo: CollectionDumpRepository | None = None,
        storage: BackupStorage | None = None,
    ) -> None:
        self._repo = repo if repo is not None else CollectionDumpRepository()
        self._storage = storage if storage is not None else BackupStorage()

    def export_all(self, collections: tuple[str, ...] = BACKED_UP_COLLECTIONS) -> dict[str, int]:
        timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")
        counts: dict[str, int] = {}
        for collection in collections:
            docs = self._repo.dump(collection)
            counts[collection] = len(docs)
            payload = json.dumps(docs, default=str).encode("utf-8")
            self._storage.write_json(f"{timestamp}/{collection}.json", payload)
        log.info("nightly backup complete", extra={"extra_fields": {"counts": counts}})
        return counts

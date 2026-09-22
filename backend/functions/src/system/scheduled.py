"""nightly_backup — exports every top-level collection to Storage as JSON.

Plain per-document JSON, not GCP's native Firestore export/import: the whole point, per
docs/RUNBOOK.md, is that a backup can be restored into the *emulator* to verify it before
ever touching production, and the native export format is only importable into a real
Firestore instance — not something the emulator can read back for a local, safe check.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from firebase_functions import scheduler_fn

from shared.core.config import get_settings
from shared.core.firebase import get_db
from shared.core.logging import get_logger
from shared.core.timestamps import from_firestore
from shared.services.storage import StorageService

log = get_logger(__name__)

# Every collection backed by a schema in architecture/schemas, plus the two internal ones
# that aren't (audit_log has no visibility/order and isn't user content, but losing the
# audit trail in a disaster is still a real loss).
_COLLECTIONS = [
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
]


def export_all_collections() -> dict[str, int]:
    """The actual export logic, separated from the trigger decorator so it's callable
    directly from a test or a one-off manual run without going through the scheduler."""
    db = get_db()
    storage = StorageService()
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")
    counts: dict[str, int] = {}

    for collection in _COLLECTIONS:
        docs = [
            {"id": snap.id, "data": from_firestore(snap.to_dict() or {})}
            for snap in db.collection(collection).stream()
        ]
        counts[collection] = len(docs)
        path = f"{timestamp}/{collection}.json"
        storage.upload_bytes(
            path,
            json.dumps(docs, default=str).encode("utf-8"),
            content_type="application/json",
            bucket=get_settings().backups_bucket,
        )

    log.info("nightly backup complete", extra={"extra_fields": {"counts": counts}})
    return counts


@scheduler_fn.on_schedule(schedule="every 24 hours", region="asia-south1", timeout_sec=300)
def nightly_backup(event: scheduler_fn.ScheduledEvent) -> None:
    export_all_collections()

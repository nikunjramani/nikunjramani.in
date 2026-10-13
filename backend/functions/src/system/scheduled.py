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

from shared.core.collections import BACKED_UP_COLLECTIONS
from shared.core.config import get_settings
from shared.core.logging import get_logger
from shared.services.storage import StorageService
from src.system.repository import BackupRepository

log = get_logger(__name__)


def export_all_collections() -> dict[str, int]:
    """The actual export logic, separated from the trigger decorator so it's callable
    directly from a test or a one-off manual run without going through the scheduler."""
    backups = BackupRepository()
    storage = StorageService()
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")
    counts: dict[str, int] = {}

    for collection in BACKED_UP_COLLECTIONS:
        docs = backups.dump(collection)
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

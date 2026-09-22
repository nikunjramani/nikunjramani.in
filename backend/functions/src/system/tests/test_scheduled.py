"""export_all_collections against a real emulator for the Firestore reads, with Storage
uploads mocked — a live backups bucket doesn't exist until Phase 6 (billing)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from google.cloud.firestore_v1 import Client

from src.system.scheduled import export_all_collections


def test_export_reads_every_configured_collection_and_uploads_json(db: Client) -> None:
    db.collection("skills").document("python").set(
        {"name": "Python", "category": "backend", "level": 5, "visibility": "public"}
    )

    fake_storage = MagicMock()
    with patch("src.system.scheduled.StorageService", return_value=fake_storage):
        counts = export_all_collections()

    assert counts["skills"] == 1
    assert fake_storage.upload_bytes.call_count == len(counts)

    skills_call = next(
        c for c in fake_storage.upload_bytes.call_args_list if c.args[0].endswith("skills.json")
    )
    uploaded = json.loads(skills_call.args[1])
    assert uploaded[0]["id"] == "python"
    assert uploaded[0]["data"]["name"] == "Python"
    assert skills_call.kwargs["bucket"] == "nikunjramani-in-backups"

    db.collection("skills").document("python").delete()


def test_export_handles_an_empty_collection(db: Client) -> None:
    fake_storage = MagicMock()
    with patch("src.system.scheduled.StorageService", return_value=fake_storage):
        counts = export_all_collections()
    assert counts["projects"] == 0
    empty_call = next(
        c for c in fake_storage.upload_bytes.call_args_list if c.args[0].endswith("projects.json")
    )
    assert json.loads(empty_call.args[1]) == []

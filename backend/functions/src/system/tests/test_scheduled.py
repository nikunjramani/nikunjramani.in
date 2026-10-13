"""export_all_collections against a real emulator for the Firestore reads, with Storage
uploads mocked — a live backups bucket doesn't exist until Phase 6 (billing).

Neither test assumes the emulator's real collections (skills, projects, ...) start empty.
They used to, and it worked by accident as long as nothing else had ever seeded the
emulator in a given run — exactly the kind of thing that breaks the first time `make dev`
is used for actual local development with `--import=./.emulator-data
--export-on-exit=./.emulator-data` persisting real seed data across restarts, which is the
whole point of that flag. A before/after delta (test 1) and a dedicated collection name
that no part of the real app ever writes to (test 2) are both robust to however much real
content happens to be sitting in Firestore when the suite runs."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from google.cloud.firestore_v1 import Client

import src.system.scheduled as scheduled_module
from src.system.scheduled import export_all_collections


def test_export_reads_every_configured_collection_and_uploads_json(db: Client) -> None:
    # A doc id unlikely to collide with real seeded data ("python", "typescript", ... are
    # exactly the kind of id a real dev environment's skills collection already has) — a
    # collision would make .set() silently overwrite the existing doc instead of adding a
    # new one, leaving the before/after delta this test checks at zero.
    doc_id = "export-test-skill-zz9k"
    before = len(list(db.collection("skills").stream()))
    db.collection("skills").document(doc_id).set(
        {"name": "Export Test Skill", "category": "backend", "level": 5, "visibility": "public"}
    )

    fake_storage = MagicMock()
    with patch("src.system.scheduled.StorageService", return_value=fake_storage):
        counts = export_all_collections()

    assert counts["skills"] == before + 1
    assert fake_storage.upload_bytes.call_count == len(counts)

    skills_call = next(
        c for c in fake_storage.upload_bytes.call_args_list if c.args[0].endswith("skills.json")
    )
    uploaded = json.loads(skills_call.args[1])
    test_entry = next(d for d in uploaded if d["id"] == doc_id)
    assert test_entry["data"]["name"] == "Export Test Skill"
    assert skills_call.kwargs["bucket"] == "nikunjramani-in-backups"

    db.collection("skills").document(doc_id).delete()


def test_export_handles_an_empty_collection(db: Client, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    # A name no schema or domain ever writes to, so it's guaranteed empty regardless of
    # whatever real seed data the rest of the collections carry — that guarantee, not
    # "projects happens to have nothing in it today", is what this test is actually for.
    scratch_collection = "scratch_empty_for_export_test"
    monkeypatch.setattr(scheduled_module, "BACKED_UP_COLLECTIONS", [scratch_collection])

    fake_storage = MagicMock()
    with patch("src.system.scheduled.StorageService", return_value=fake_storage):
        counts = export_all_collections()

    assert counts[scratch_collection] == 0
    empty_call = next(
        c
        for c in fake_storage.upload_bytes.call_args_list
        if c.args[0].endswith(f"{scratch_collection}.json")
    )
    assert json.loads(empty_call.args[1]) == []

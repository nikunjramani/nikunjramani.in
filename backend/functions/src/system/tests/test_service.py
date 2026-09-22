from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from google.cloud.firestore_v1 import Client

from shared.core.errors import NotFoundError
from src.system.service import SystemService


def test_get_resume_url_returns_the_stored_url(db: Client) -> None:
    db.collection("profile").document("main").set(
        {"name": "N", "headline": "H", "visibility": "public", "resumeUrl": "https://x.com/r.pdf"}
    )
    svc = SystemService(db)
    assert svc.get_resume_url() == "https://x.com/r.pdf"
    db.collection("profile").document("main").delete()


def test_get_resume_url_404s_when_profile_has_no_resume(db: Client) -> None:
    db.collection("profile").document("main").set(
        {"name": "N", "headline": "H", "visibility": "public"}
    )
    svc = SystemService(db)
    with pytest.raises(NotFoundError):
        svc.get_resume_url()
    db.collection("profile").document("main").delete()


def test_get_resume_url_404s_when_profile_does_not_exist(db: Client) -> None:
    svc = SystemService(db)
    with pytest.raises(NotFoundError):
        svc.get_resume_url()


def test_record_resume_download_increments_atomically(db: Client) -> None:
    svc = SystemService(db)
    doc_ref = db.collection("system_stats").document("resume")
    doc_ref.delete()

    svc.record_resume_download()
    svc.record_resume_download()
    svc.record_resume_download()

    data = doc_ref.get().to_dict()
    assert data is not None
    assert data["downloadCount"] == 3
    doc_ref.delete()


def test_list_audit_log_filters_by_collection_and_doc_id_and_orders_newest_first(
    db: Client,
) -> None:
    ref = db.collection("audit_log")

    def _entry(action: str, collection: str, doc_id: str, at: str) -> dict[str, str]:
        return {
            "actor": "u1",
            "action": action,
            "collection": collection,
            "docId": doc_id,
            "at": at,
        }

    entries = [
        _entry("create", "projects", "p1", "2026-01-01T00:00:00Z"),
        _entry("update", "projects", "p1", "2026-01-03T00:00:00Z"),
        _entry("update", "projects", "p2", "2026-01-02T00:00:00Z"),
        _entry("update", "skills", "s1", "2026-01-04T00:00:00Z"),
    ]
    docs = [ref.document() for _ in entries]
    for doc, entry in zip(docs, entries, strict=True):
        doc.set(entry)

    try:
        svc = SystemService(db)
        result = svc.list_audit_log(collection="projects", doc_id="p1")
        assert [e["action"] for e in result] == ["update", "create"]  # newest first
        assert all(e["docId"] == "p1" for e in result)

        by_collection = svc.list_audit_log(collection="skills")
        assert len(by_collection) == 1
        assert by_collection[0]["docId"] == "s1"

        limited = svc.list_audit_log(collection="projects", limit=1)
        assert len(limited) == 1
        assert limited[0]["docId"] == "p1" and limited[0]["at"].startswith("2026-01-03")
    finally:
        for doc in docs:
            doc.delete()


def test_record_resume_download_never_raises() -> None:
    """Counting a download must never break the download itself — even against a client
    that fails outright."""
    broken_db = MagicMock()
    broken_db.collection.side_effect = RuntimeError("boom")
    svc = SystemService(broken_db)
    svc.record_resume_download()  # must not raise

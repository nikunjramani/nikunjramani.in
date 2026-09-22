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


def test_record_resume_download_never_raises() -> None:
    """Counting a download must never break the download itself — even against a client
    that fails outright."""
    broken_db = MagicMock()
    broken_db.collection.side_effect = RuntimeError("boom")
    svc = SystemService(broken_db)
    svc.record_resume_download()  # must not raise

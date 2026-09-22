from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from google.cloud.firestore_v1 import Client

from shared.core.errors import ValidationError
from src.media.repository import MediaRepository
from src.media.service import MediaService


def _service(db: Client, collection_name: str, storage: MagicMock) -> MediaService:
    class ScratchRepo(MediaRepository):
        collection = collection_name

    return MediaService(repo=ScratchRepo(db), storage=storage)


def test_request_upload_rejects_bad_content_type(db: Client, clean_collection: str) -> None:
    svc = _service(db, clean_collection, MagicMock())
    with pytest.raises(ValidationError):
        svc.request_upload(content_type="application/pdf", size_bytes=100)


def test_request_upload_returns_the_signed_url_and_path(db: Client, clean_collection: str) -> None:
    storage = MagicMock()
    storage.create_signed_upload_url.return_value = "https://signed.example.com/x"
    svc = _service(db, clean_collection, storage)

    result = svc.request_upload(content_type="image/webp", size_bytes=1000)
    assert result["uploadUrl"] == "https://signed.example.com/x"
    assert result["path"].startswith("public/media/")


def test_create_from_processed_upload_persists_the_asset(db: Client, clean_collection: str) -> None:
    svc = _service(db, clean_collection, MagicMock())
    record = svc.create_from_processed_upload(
        original_path="public/media/1/original.webp",
        url="https://x/processed.webp",
        thumbnail_url="https://x/thumbnail.webp",
        width=1600,
        height=900,
        blurhash="LGF5]+Yk",
        content_type="image/webp",
        size_bytes=12345,
        uploaded_by="uid-1",
    )
    assert record.data.width == 1600
    assert record.data.blurhash == "LGF5]+Yk"

    fetched = svc.get(record.id)
    assert fetched.data.uploadedBy == "uid-1"


def test_delete_removes_both_storage_and_firestore(db: Client, clean_collection: str) -> None:
    storage = MagicMock()
    svc = _service(db, clean_collection, storage)
    record = svc.create_from_processed_upload(
        original_path="public/media/1/original.webp",
        url="https://x/processed.webp",
        thumbnail_url="https://x/thumbnail.webp",
        width=100,
        height=100,
        blurhash="x",
        content_type="image/webp",
        size_bytes=1,
        uploaded_by=None,
    )
    svc.delete(record.id)
    storage.delete.assert_called_once_with("public/media/1/original.webp")
    assert svc.repo.get(record.id) is None


def test_delete_still_removes_firestore_record_if_storage_delete_fails(
    db: Client, clean_collection: str
) -> None:
    """An already-gone Storage object should not block cleaning up the dangling record."""
    storage = MagicMock()
    storage.delete.side_effect = Exception("not found")
    svc = _service(db, clean_collection, storage)
    record = svc.create_from_processed_upload(
        original_path="public/media/1/original.webp",
        url="https://x/processed.webp",
        thumbnail_url="https://x/thumbnail.webp",
        width=100,
        height=100,
        blurhash="x",
        content_type="image/webp",
        size_bytes=1,
        uploaded_by=None,
    )
    svc.delete(record.id)  # must not raise
    assert svc.repo.get(record.id) is None

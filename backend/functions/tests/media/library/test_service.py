"""LibraryService against the Firestore emulator (skips without it), Storage mocked."""

from __future__ import annotations

from unittest.mock import MagicMock, call

from google.cloud.firestore_v1 import Client

from kernel.timestamps import now_iso, to_firestore
from shared.generated import MediaAsset
from src.media.library.repository import LibraryRepository
from src.media.library.service import LibraryService

CLAIMS = {"uid": "admin-1", "email": "admin@example.com", "admin": True}


def _service(db: Client, collection_name: str, storage: MagicMock) -> LibraryService:
    class ScratchRepo(LibraryRepository):
        collection = collection_name

    return LibraryService(repo=ScratchRepo(db), storage=storage, audit=MagicMock())


def _seed(svc: LibraryService, asset_id: str = "a1") -> None:
    """Assets are created by media/processing; here they're written directly."""
    asset = MediaAsset.model_validate(
        {
            "url": "https://x/processed.webp",
            "path": f"uploads/media/{asset_id}/original.webp",
            "thumbnailUrl": "https://x/thumbnail.webp",
            "width": 100,
            "height": 100,
            "uploadedAt": now_iso(),
        }
    )
    ref = svc.repo.db.collection(svc.repo.collection).document(asset_id)
    ref.set(to_firestore(asset.model_dump(mode="json", exclude_none=True)))


def test_update_metadata_sets_alt_and_caption(db: Client, clean_collection: str) -> None:
    svc = _service(db, clean_collection, MagicMock())
    _seed(svc)
    updated = svc.update_metadata("a1", alt="A dashboard screenshot", caption="v2", claims=CLAIMS)
    assert updated.data.alt == "A dashboard screenshot"
    assert svc.get("a1").data.caption == "v2"


def test_delete_removes_storage_objects_and_the_document(db: Client, clean_collection: str) -> None:
    storage = MagicMock()
    svc = _service(db, clean_collection, storage)
    _seed(svc)
    svc.delete("a1", CLAIMS)
    assert storage.delete.call_args_list == [
        call("uploads/media/a1/original.webp"),
        call("public/media/a1/processed.webp"),
        call("public/media/a1/thumbnail.webp"),
    ]
    assert svc.repo.get("a1") is None


def test_delete_survives_already_missing_storage_objects(db: Client, clean_collection: str) -> None:
    storage = MagicMock()
    storage.delete.side_effect = Exception("not found")
    svc = _service(db, clean_collection, storage)
    _seed(svc)
    svc.delete("a1", CLAIMS)  # must not raise
    assert storage.delete.call_count == 3
    assert svc.repo.get("a1") is None


def test_list_all_returns_every_asset(db: Client, clean_collection: str) -> None:
    svc = _service(db, clean_collection, MagicMock())
    _seed(svc, "a1")
    _seed(svc, "a2")
    assert {r.id for r in svc.list_all()} == {"a1", "a2"}

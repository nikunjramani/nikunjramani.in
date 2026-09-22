"""ProjectService.duplicate — the one thing this domain adds beyond the generic CRUD
already proven in shared/tests/test_crud.py."""

from __future__ import annotations

from google.cloud.firestore_v1 import Client

from shared.generated import Project
from src.projects.repository import ProjectRepository
from src.projects.service import ProjectService

CLAIMS = {"uid": "admin-1", "email": "admin@example.com", "admin": True}


def _project(slug: str, **overrides: object) -> Project:
    data: dict[str, object] = {
        "slug": slug,
        "title": "Realtime Inventory Sync",
        "summary": "Kept stock counts consistent.",
        "kind": "personal",
        "status": "shipped",
        "visibility": "public",
        "featured": True,
    }
    data.update(overrides)
    return Project.model_validate(data)


def _service(db: Client, collection_name: str) -> ProjectService:
    class ScratchRepo(ProjectRepository):
        collection = collection_name

    return ProjectService(repo=ScratchRepo(db))


def test_duplicate_resets_publish_state_and_gets_a_new_slug(
    db: Client, clean_collection: str
) -> None:
    svc = _service(db, clean_collection)
    original = svc.create(_project("inventory-sync"), CLAIMS, doc_id="inventory-sync")
    copy = svc.duplicate(original.id, CLAIMS)

    assert copy.id == "inventory-sync-copy"
    assert copy.data.title == "Realtime Inventory Sync (copy)"
    assert copy.data.visibility == "draft"
    assert copy.data.featured is False
    assert svc.repo.require("inventory-sync").data.featured is True  # original untouched


def test_duplicate_twice_gets_distinct_slugs(db: Client, clean_collection: str) -> None:
    svc = _service(db, clean_collection)
    svc.create(_project("aa"), CLAIMS, doc_id="aa")
    first = svc.duplicate("aa", CLAIMS)
    second = svc.duplicate("aa", CLAIMS)
    assert first.id == "aa-copy"
    assert second.id == "aa-copy-2"


def test_duplicate_missing_project_is_404(db: Client, clean_collection: str) -> None:
    import pytest

    from shared.core.errors import NotFoundError

    svc = _service(db, clean_collection)
    with pytest.raises(NotFoundError):
        svc.duplicate("nope", CLAIMS)

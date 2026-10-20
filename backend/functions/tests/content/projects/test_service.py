"""What ProjectService adds beyond the generic CRUD already proven in
tests/kernel/crud/test_service.py: duplicate, unlisted pages, confidential clients and
reserved slugs."""

from __future__ import annotations

import pytest
from google.cloud.firestore_v1 import Client

from kernel.errors import NotFoundError, ValidationError
from shared.generated import Project
from src.content.projects.repository import ProjectRepository
from src.content.projects.service import ProjectService

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

    from kernel.errors import NotFoundError

    svc = _service(db, clean_collection)
    with pytest.raises(NotFoundError):
        svc.duplicate("nope", CLAIMS)


def test_get_public_serves_unlisted_but_list_public_never_lists_it(
    db: Client, clean_collection: str
) -> None:
    svc = _service(db, clean_collection)
    svc.create(_project("shown"), CLAIMS, doc_id="shown")
    svc.create(_project("by-link", visibility="unlisted"), CLAIMS, doc_id="by-link")
    svc.create(_project("wip", visibility="draft"), CLAIMS, doc_id="wip")

    assert [r.id for r in svc.list_public()] == ["shown"]
    assert svc.get_public("by-link").id == "by-link"
    with pytest.raises(NotFoundError):
        svc.get_public("wip")


def test_public_reads_strip_a_confidential_client(db: Client, clean_collection: str) -> None:
    svc = _service(db, clean_collection)
    client = {
        "name": "Acme Logistics",
        "logoUrl": "https://example.com/acme.png",
        "confidential": True,
        "publicLabel": "a logistics client",
    }
    svc.create(_project("secret", client=client), CLAIMS, doc_id="secret")

    for record in (svc.get_public("secret"), svc.list_public()[0]):
        assert record.data.client is not None
        assert record.data.client.name is None
        assert record.data.client.logoUrl is None
        assert record.data.client.publicLabel == "a logistics client"
    # The admin read is untouched.
    assert svc.get("secret").data.client.name == "Acme Logistics"  # type: ignore[union-attr]


def test_reserved_slugs_are_refused(db: Client, clean_collection: str) -> None:
    svc = _service(db, clean_collection)
    for slug in ("public", "reorder"):
        with pytest.raises(ValidationError):
            svc.create(_project(slug), CLAIMS, doc_id=slug)

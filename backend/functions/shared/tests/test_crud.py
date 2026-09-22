"""ContentService against a real emulator-backed repository.

Uses Skill as the guinea pig model (small, has visibility/order, no slug) — the CRUD
mechanics don't depend on which schema, so one model's worth of coverage proves the
pattern every content domain will reuse.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from google.cloud.firestore_v1 import Client, DocumentSnapshot

from shared.core.errors import ConflictError, NotFoundError, ValidationError
from shared.crud import ContentService, deep_merge
from shared.generated import Skill
from shared.repositories.base import BaseRepository


class SkillRepository(BaseRepository[Skill]):
    collection = "_test_scratch"
    model = Skill


CLAIMS = {"uid": "admin-1", "email": "admin@example.com", "admin": True}


def _dict(snapshot: DocumentSnapshot) -> dict[str, Any]:
    data = snapshot.to_dict()
    assert data is not None
    return data


@pytest.fixture
def service(db: Client, clean_collection: str) -> ContentService[Skill]:
    return ContentService(SkillRepository(db), bust_cache=MagicMock())


def _skill(**overrides: object) -> Skill:
    defaults: dict[str, object] = {
        "name": "Python",
        "category": "backend",
        "level": 4,
        "visibility": "public",
    }
    defaults.update(overrides)
    return Skill(**defaults)  # type: ignore[arg-type]


# ── deep_merge ──────────────────────────────────────────────────────


def test_deep_merge_overwrites_scalars() -> None:
    assert deep_merge({"a": 1, "b": 2}, {"b": 3}) == {"a": 1, "b": 3}


def test_deep_merge_recurses_into_nested_objects() -> None:
    target = {"content": {"overview": "x", "problem": "y"}}
    patch = {"content": {"problem": "z"}}
    assert deep_merge(target, patch) == {"content": {"overview": "x", "problem": "z"}}


def test_deep_merge_null_deletes_a_key() -> None:
    assert deep_merge({"a": 1, "b": 2}, {"b": None}) == {"a": 1}


def test_deep_merge_replaces_lists_wholesale() -> None:
    assert deep_merge({"tags": ["a", "b"]}, {"tags": ["c"]}) == {"tags": ["c"]}


# ── create ───────────────────────────────────────────────────────────


def test_create_stamps_audit_fields(service: ContentService[Skill]) -> None:
    record = service.create(_skill(), CLAIMS)
    assert record.data.audit is not None
    assert record.data.audit.createdBy == "admin-1"
    assert record.data.audit.createdAt == record.data.audit.updatedAt
    assert record.data.audit.publishedAt is not None  # created already public


def test_create_does_not_publish_a_draft(service: ContentService[Skill]) -> None:
    record = service.create(_skill(visibility="draft"), CLAIMS)
    assert record.data.audit is not None
    assert record.data.audit.publishedAt is None


def test_create_with_explicit_id_conflicts_on_reuse(service: ContentService[Skill]) -> None:
    service.create(_skill(), CLAIMS, doc_id="python")
    with pytest.raises(ConflictError):
        service.create(_skill(), CLAIMS, doc_id="python")


def test_create_audits_and_busts_cache(service: ContentService[Skill]) -> None:
    service.create(_skill(), CLAIMS)
    audit_entries = list(service.repo.db.collection("audit_log").stream())
    assert len(audit_entries) == 1
    assert _dict(audit_entries[0])["action"] == "create"
    service._bust_cache.assert_called_once_with("_test_scratch")  # type: ignore[attr-defined]


# ── patch ────────────────────────────────────────────────────────────


def test_patch_is_a_merge_not_a_replace(service: ContentService[Skill]) -> None:
    record = service.create(_skill(blurb="original"), CLAIMS)
    updated = service.patch(record.id, {"level": 5}, CLAIMS)
    assert updated.data.level == 5
    assert updated.data.blurb == "original"


def test_patch_missing_document_is_404(service: ContentService[Skill]) -> None:
    with pytest.raises(NotFoundError):
        service.patch("nope", {"level": 1}, CLAIMS)


def test_patch_updates_the_timestamp(service: ContentService[Skill]) -> None:
    record = service.create(_skill(), CLAIMS)
    audit = record.data.audit
    assert audit is not None and audit.updatedAt is not None
    before = audit.updatedAt
    updated = service.patch(record.id, {"level": 5}, CLAIMS)
    updated_audit = updated.data.audit
    assert updated_audit is not None and updated_audit.updatedAt is not None
    assert updated_audit.updatedAt >= before


def test_patch_publish_transition_sets_published_at(service: ContentService[Skill]) -> None:
    record = service.create(_skill(visibility="draft"), CLAIMS)
    assert record.data.audit.publishedAt is None  # type: ignore[union-attr]
    published = service.patch(record.id, {"visibility": "public"}, CLAIMS)
    assert published.data.audit.publishedAt is not None  # type: ignore[union-attr]

    # .stream() gives no ordering guarantee — auto-generated document ids are not
    # chronological — so filter to this record and sort by "at" explicitly rather than
    # assuming stream order matches write order.
    audit_entries = [_dict(e) for e in service.repo.db.collection("audit_log").stream()]
    this_record = sorted(
        (e for e in audit_entries if e["docId"] == record.id), key=lambda e: e["at"]
    )
    assert [e["action"] for e in this_record] == ["create", "publish"]


def test_patch_republish_keeps_the_original_published_at(service: ContentService[Skill]) -> None:
    record = service.create(_skill(visibility="draft"), CLAIMS)
    first = service.patch(record.id, {"visibility": "public"}, CLAIMS)
    first_published_at = first.data.audit.publishedAt  # type: ignore[union-attr]
    unpublished = service.patch(record.id, {"visibility": "draft"}, CLAIMS)
    republished = service.patch(unpublished.id, {"visibility": "public"}, CLAIMS)
    assert republished.data.audit.publishedAt == first_published_at  # type: ignore[union-attr]


def test_patch_rejects_changing_the_slug(db: Client, clean_collection: str) -> None:
    from shared.generated import Project

    class ProjectRepository(BaseRepository[Project]):
        collection = clean_collection
        model = Project

    svc: ContentService[Project] = ContentService(ProjectRepository(db), bust_cache=MagicMock())
    proj: Project = Project.model_validate(
        {
            "slug": "aa",
            "title": "A",
            "summary": "s",
            "kind": "personal",
            "status": "shipped",
            "visibility": "public",
        }
    )
    record = svc.create(proj, CLAIMS, doc_id=proj.slug)
    with pytest.raises(ValidationError):
        svc.patch(record.id, {"slug": "b"}, CLAIMS)


def test_patch_rejects_a_value_the_schema_forbids(service: ContentService[Skill]) -> None:
    record = service.create(_skill(), CLAIMS)
    with pytest.raises(ValidationError):
        service.patch(record.id, {"level": 99}, CLAIMS)  # level is 1-5


# ── delete ───────────────────────────────────────────────────────────


def test_delete_records_the_before_state_in_the_audit_log(service: ContentService[Skill]) -> None:
    record = service.create(_skill(name="Rust"), CLAIMS)
    service.delete(record.id, CLAIMS)
    assert service.repo.get(record.id) is None

    audit_entries = [_dict(e) for e in service.repo.db.collection("audit_log").stream()]
    delete_entry = next(e for e in audit_entries if e["action"] == "delete")
    assert delete_entry["before"]["name"] == "Rust"
    assert delete_entry["after"] is None


def test_delete_missing_document_is_404(service: ContentService[Skill]) -> None:
    with pytest.raises(NotFoundError):
        service.delete("nope", CLAIMS)


# ── reorder ──────────────────────────────────────────────────────────


def test_reorder_rejects_an_unknown_id(service: ContentService[Skill]) -> None:
    a = service.create(_skill(name="A"), CLAIMS)
    with pytest.raises(ValidationError):
        service.reorder([a.id, "does-not-exist"], CLAIMS)


def test_reorder_rejects_a_duplicate_id(service: ContentService[Skill]) -> None:
    a = service.create(_skill(name="A"), CLAIMS)
    with pytest.raises(ValidationError):
        service.reorder([a.id, a.id], CLAIMS)


def test_reorder_applies_the_new_order(service: ContentService[Skill]) -> None:
    a = service.create(_skill(name="A"), CLAIMS)
    b = service.create(_skill(name="B"), CLAIMS)
    service.reorder([b.id, a.id], CLAIMS)
    ordered = service.list_records()
    assert [r.data.name for r in ordered] == ["B", "A"]

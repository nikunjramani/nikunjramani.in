"""CrudService against a real emulator-backed repository.

Uses Skill as the guinea pig model (small, has visibility/order, no slug) — the CRUD
mechanics don't depend on which schema, so one model's worth of coverage proves the
pattern every content domain will reuse.
"""

from __future__ import annotations

from typing import Any

import pytest
from google.cloud.firestore_v1 import Client, DocumentSnapshot

from kernel.crud.repository import BaseRepository
from kernel.crud.service import CrudService, deep_merge
from kernel.errors import ConflictError, NotFoundError, ValidationError
from kernel.security import Actor
from shared.generated import Skill


class SkillRepository(BaseRepository[Skill]):
    collection = "_test_scratch"
    model = Skill


ACTOR = Actor(uid="admin-1", email="admin@example.com")


def _dict(snapshot: DocumentSnapshot) -> dict[str, Any]:
    data = snapshot.to_dict()
    assert data is not None
    return data


@pytest.fixture
def service(db: Client, clean_collection: str) -> CrudService[Skill]:
    return CrudService(SkillRepository(db))


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


def test_create_stamps_audit_fields(service: CrudService[Skill]) -> None:
    record = service.create(_skill(), ACTOR)
    assert record.data.audit is not None
    assert record.data.audit.createdBy == "admin-1"
    assert record.data.audit.createdAt == record.data.audit.updatedAt
    assert record.data.audit.publishedAt is not None  # created already public


def test_create_does_not_publish_a_draft(service: CrudService[Skill]) -> None:
    record = service.create(_skill(visibility="draft"), ACTOR)
    assert record.data.audit is not None
    assert record.data.audit.publishedAt is None


def test_create_with_explicit_id_conflicts_on_reuse(service: CrudService[Skill]) -> None:
    service.create(_skill(), ACTOR, doc_id="python")
    with pytest.raises(ConflictError):
        service.create(_skill(), ACTOR, doc_id="python")


def test_create_writes_an_audit_entry(service: CrudService[Skill]) -> None:
    service.create(_skill(), ACTOR)
    audit_entries = list(service.repo.db.collection("audit_log").stream())
    assert len(audit_entries) == 1
    assert _dict(audit_entries[0])["action"] == "create"


# ── patch ────────────────────────────────────────────────────────────


def test_patch_is_a_merge_not_a_replace(service: CrudService[Skill]) -> None:
    record = service.create(_skill(blurb="original"), ACTOR)
    updated = service.patch(record.id, {"level": 5}, ACTOR)
    assert updated.data.level == 5
    assert updated.data.blurb == "original"


def test_patch_missing_document_is_404(service: CrudService[Skill]) -> None:
    with pytest.raises(NotFoundError):
        service.patch("nope", {"level": 1}, ACTOR)


def test_patch_updates_the_timestamp(service: CrudService[Skill]) -> None:
    record = service.create(_skill(), ACTOR)
    audit = record.data.audit
    assert audit is not None and audit.updatedAt is not None
    before = audit.updatedAt
    updated = service.patch(record.id, {"level": 5}, ACTOR)
    updated_audit = updated.data.audit
    assert updated_audit is not None and updated_audit.updatedAt is not None
    assert updated_audit.updatedAt >= before


def test_patch_publish_transition_sets_published_at(service: CrudService[Skill]) -> None:
    record = service.create(_skill(visibility="draft"), ACTOR)
    assert record.data.audit.publishedAt is None  # type: ignore[union-attr]
    published = service.patch(record.id, {"visibility": "public"}, ACTOR)
    assert published.data.audit.publishedAt is not None  # type: ignore[union-attr]

    # .stream() gives no ordering guarantee — auto-generated document ids are not
    # chronological — so filter to this record and sort by "at" explicitly rather than
    # assuming stream order matches write order.
    audit_entries = [_dict(e) for e in service.repo.db.collection("audit_log").stream()]
    this_record = sorted(
        (e for e in audit_entries if e["docId"] == record.id), key=lambda e: e["at"]
    )
    assert [e["action"] for e in this_record] == ["create", "publish"]


def test_patch_republish_keeps_the_original_published_at(service: CrudService[Skill]) -> None:
    record = service.create(_skill(visibility="draft"), ACTOR)
    first = service.patch(record.id, {"visibility": "public"}, ACTOR)
    first_published_at = first.data.audit.publishedAt  # type: ignore[union-attr]
    unpublished = service.patch(record.id, {"visibility": "draft"}, ACTOR)
    republished = service.patch(unpublished.id, {"visibility": "public"}, ACTOR)
    assert republished.data.audit.publishedAt == first_published_at  # type: ignore[union-attr]


# ── upsert (singletons) ───────────────────────────────────────────


def test_upsert_keeps_created_and_first_published_stamps(service: CrudService[Skill]) -> None:
    first = service.upsert("main", _skill(), ACTOR)
    second = service.upsert("main", _skill(name="Renamed"), ACTOR)
    assert first.data.audit is not None
    assert second.data.audit is not None
    assert second.data.audit.createdAt == first.data.audit.createdAt
    assert second.data.audit.publishedAt == first.data.audit.publishedAt
    assert second.data.name == "Renamed"


def test_upsert_records_publish_and_unpublish(service: CrudService[Skill]) -> None:
    service.upsert("main", _skill(visibility="draft"), ACTOR)
    published = service.upsert("main", _skill(visibility="public"), ACTOR)
    service.upsert("main", _skill(visibility="draft"), ACTOR)
    assert published.data.audit is not None
    assert published.data.audit.publishedAt is not None
    actions = sorted(
        (_dict(e) for e in service.repo.db.collection("audit_log").stream()),
        key=lambda e: e["at"],
    )
    assert [e["action"] for e in actions] == ["create", "publish", "unpublish"]


def test_patch_rejects_changing_the_slug(db: Client, clean_collection: str) -> None:
    from shared.generated import Project

    class ProjectRepository(BaseRepository[Project]):
        collection = clean_collection
        model = Project

    svc: CrudService[Project] = CrudService(ProjectRepository(db))
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
    record = svc.create(proj, ACTOR, doc_id=proj.slug)
    with pytest.raises(ValidationError):
        svc.patch(record.id, {"slug": "b"}, ACTOR)


def test_patch_rejects_a_value_the_schema_forbids(service: CrudService[Skill]) -> None:
    record = service.create(_skill(), ACTOR)
    with pytest.raises(ValidationError):
        service.patch(record.id, {"level": 99}, ACTOR)  # level is 1-5


# ── delete ───────────────────────────────────────────────────────────


def test_delete_records_the_before_state_in_the_audit_log(service: CrudService[Skill]) -> None:
    record = service.create(_skill(name="Rust"), ACTOR)
    service.delete(record.id, ACTOR)
    assert service.repo.get(record.id) is None

    audit_entries = [_dict(e) for e in service.repo.db.collection("audit_log").stream()]
    delete_entry = next(e for e in audit_entries if e["action"] == "delete")
    assert delete_entry["before"]["name"] == "Rust"
    assert delete_entry["after"] is None


def test_delete_missing_document_is_404(service: CrudService[Skill]) -> None:
    with pytest.raises(NotFoundError):
        service.delete("nope", ACTOR)


# ── reorder ──────────────────────────────────────────────────────────


def test_reorder_rejects_an_unknown_id(service: CrudService[Skill]) -> None:
    a = service.create(_skill(name="A"), ACTOR)
    with pytest.raises(ValidationError):
        service.reorder([a.id, "does-not-exist"], ACTOR)


def test_reorder_rejects_a_duplicate_id(service: CrudService[Skill]) -> None:
    a = service.create(_skill(name="A"), ACTOR)
    with pytest.raises(ValidationError):
        service.reorder([a.id, a.id], ACTOR)


def test_reorder_applies_the_new_order(service: CrudService[Skill]) -> None:
    a = service.create(_skill(name="A"), ACTOR)
    b = service.create(_skill(name="B"), ACTOR)
    service.reorder([b.id, a.id], ACTOR)
    ordered = service.list_records()
    assert [r.data.name for r in ordered] == ["B", "A"]


# ── public reads ────────────────────────────────────────────────────


def test_list_public_returns_only_public_in_order(service: CrudService[Skill]) -> None:
    service.create(_skill(name="B", order=1), ACTOR)
    service.create(_skill(name="A", order=0), ACTOR)
    service.create(_skill(name="Draft", visibility="draft"), ACTOR)
    service.create(_skill(name="Hidden", visibility="unlisted"), ACTOR)

    assert [r.data.name for r in service.list_public()] == ["A", "B"]


def test_public_reads_drop_the_audit_block(service: CrudService[Skill]) -> None:
    created = service.create(_skill(), ACTOR)
    assert created.data.audit is not None

    assert all(r.data.audit is None for r in service.list_public())
    assert service.get_public(created.id).data.audit is None


def test_get_public_404s_for_draft_unlisted_and_missing(service: CrudService[Skill]) -> None:
    draft = service.create(_skill(visibility="draft"), ACTOR)
    unlisted = service.create(_skill(visibility="unlisted"), ACTOR)
    for doc_id in (draft.id, unlisted.id, "does-not-exist"):
        with pytest.raises(NotFoundError):
            service.get_public(doc_id)

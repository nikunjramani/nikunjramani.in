"""Integration tests for BaseRepository against the real Firestore emulator.

These exist because mypy proves the types line up, not that Firestore actually behaves
the way the code assumes — visibility filters, ordering and reorder
batches are exactly the kind of thing that type-checks cleanly and is wrong at runtime.
"""

from __future__ import annotations

import pytest
from google.api_core.exceptions import NotFound
from google.cloud.firestore_v1 import Client

from kernel.audit import AuditEntry
from kernel.crud.repository import BaseRepository
from kernel.errors import NotFoundError
from kernel.security import Actor
from shared.generated import Skill


class SkillRepository(BaseRepository[Skill]):
    collection = "_test_scratch"
    model = Skill


def _skill(name: str, *, order: int = 0, visibility: str = "public") -> Skill:
    return Skill(name=name, category="backend", level=4, order=order, visibility=visibility)  # type: ignore[arg-type]


def test_create_and_get_round_trip(db: Client, clean_collection: str) -> None:
    repo = SkillRepository(db)
    record = repo.create(_skill("Python"))

    fetched = repo.get(record.id)
    assert fetched is not None
    assert fetched.data.name == "Python"
    assert fetched.data.level == 4


def test_get_missing_returns_none(db: Client, clean_collection: str) -> None:
    repo = SkillRepository(db)
    assert repo.get("does-not-exist") is None


def test_require_missing_raises(db: Client, clean_collection: str) -> None:
    repo = SkillRepository(db)
    try:
        repo.require("does-not-exist")
        raise AssertionError("expected NotFoundError")
    except NotFoundError:
        pass


def test_create_with_explicit_doc_id(db: Client, clean_collection: str) -> None:
    repo = SkillRepository(db)
    record = repo.create(_skill("Rust"), doc_id="rust")
    assert record.id == "rust"
    assert repo.get("rust") is not None


def test_delete_requires_existing(db: Client, clean_collection: str) -> None:
    repo = SkillRepository(db)
    record = repo.create(_skill("C++"))
    repo.delete(record.id)
    assert repo.get(record.id) is None

    try:
        repo.delete(record.id)
        raise AssertionError("expected NotFoundError on double delete")
    except NotFoundError:
        pass


def test_list_all_filters_by_visibility_and_sorts_by_order(
    db: Client, clean_collection: str
) -> None:
    repo = SkillRepository(db)
    repo.create(_skill("Third", order=3))
    repo.create(_skill("Hidden", order=1, visibility="draft"))
    repo.create(_skill("First", order=1))
    repo.create(_skill("Second", order=2))

    published = repo.list_all(visibility="public")
    assert [r.data.name for r in published] == ["First", "Second", "Third"]

    everything = repo.list_all()
    assert len(everything) == 4


def test_reorder_reassigns_order_in_one_batch(db: Client, clean_collection: str) -> None:
    repo = SkillRepository(db)
    a = repo.create(_skill("A", order=0))
    b = repo.create(_skill("B", order=1))
    c = repo.create(_skill("C", order=2))

    repo.reorder([c.id, a.id, b.id])

    reordered = repo.list_all()
    assert [r.data.name for r in reordered] == ["C", "A", "B"]


def test_timestamps_round_trip_through_firestore(db: Client, clean_collection: str) -> None:
    """The trap this guards against: Firestore returns its own Timestamp type on read,
    and if from_firestore() did not convert it back, Pydantic validation of AwareDatetime
    fields (like Experience.startDate is NOT this — audit.at is) would fail or silently
    hold a non-ISO value."""
    from shared.generated import AuditLog

    class AuditRepo(BaseRepository[AuditLog]):
        collection = "_test_scratch"
        model = AuditLog

    repo = AuditRepo(db)
    entry = AuditLog(
        actor="uid-1",
        action="create",  # type: ignore[arg-type]
        collection="projects",
        at="2026-01-05T10:00:00+00:00",  # type: ignore[arg-type]
    )
    record = repo.create(entry)
    fetched = repo.require(record.id)
    assert fetched.data.at.year == 2026
    assert fetched.data.at.month == 1


def test_a_write_and_its_audit_entry_commit_together(db: Client, clean_collection: str) -> None:
    repo = SkillRepository(db)
    entry = AuditEntry(Actor(uid="admin-1"), "create", repo.collection, "go", None, {"n": 1})

    repo.create(_skill("Go"), doc_id="go", audit=entry)
    repo.delete(
        "go",
        audit=AuditEntry(Actor(uid="admin-1"), "delete", repo.collection, "go", {"n": 1}, None),
    )

    trail = [s.to_dict() or {} for s in db.collection("audit_log").stream()]
    assert sorted(e["action"] for e in trail) == ["create", "delete"]
    assert all(e["actor"] == "admin-1" and e["docId"] == "go" for e in trail)


def test_a_failed_write_leaves_no_audit_entry(db: Client, clean_collection: str) -> None:
    """The batch is all-or-nothing: an update of a missing document fails the commit, and
    the entry staged beside it is never written."""
    repo = SkillRepository(db)
    entry = AuditEntry(Actor(uid="admin-1"), "reorder", repo.collection, None, None, {"ids": []})

    with pytest.raises(NotFound):
        repo.reorder(["does-not-exist"], audit=entry)

    assert list(db.collection("audit_log").stream()) == []

"""CollectionDumpRepository against the Firestore emulator (skips without it)."""

from __future__ import annotations

from google.cloud.firestore_v1 import Client

from src.ops.backup.repository import CollectionDumpRepository


def test_dump_returns_every_document_with_its_id(db: Client, clean_collection: str) -> None:
    db.collection(clean_collection).document("a").set({"name": "A"})
    db.collection(clean_collection).document("b").set({"name": "B"})
    dumped = CollectionDumpRepository(db).dump(clean_collection)
    assert sorted(d["id"] for d in dumped) == ["a", "b"]
    assert {d["data"]["name"] for d in dumped} == {"A", "B"}


def test_dump_of_an_empty_collection_is_empty(db: Client, clean_collection: str) -> None:
    assert CollectionDumpRepository(db).dump(clean_collection) == []

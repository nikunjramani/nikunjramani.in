from __future__ import annotations

from google.cloud.firestore_v1 import Client

from shared.core.timestamps import now_iso
from shared.generated import ContactMessage
from src.messages.repository import MessageRepository
from src.messages.service import MessageService


def _service(db: Client, collection_name: str) -> MessageService:
    class ScratchRepo(MessageRepository):
        collection = collection_name

    return MessageService(repo=ScratchRepo(db))


def _message(name: str, **overrides: object) -> ContactMessage:
    # createdAt set explicitly, matching how ContactService.submit() actually creates a
    # message in production — a fixture that skipped it would hide the bug it's guarding
    # against instead of proving the fix (see test_a_message_missing_created_at_still_appears).
    data: dict[str, object] = {
        "name": name,
        "email": "a@example.com",
        "message": "hi",
        "createdAt": now_iso(),
    }
    data.update(overrides)
    return ContactMessage.model_validate(data)


def test_list_all_returns_everything_by_default(db: Client, clean_collection: str) -> None:
    svc = _service(db, clean_collection)
    svc.repo.create(_message("A"))
    svc.repo.create(_message("B", read=True))
    assert len(svc.list_all()) == 2


def test_list_all_can_filter_to_unread(db: Client, clean_collection: str) -> None:
    svc = _service(db, clean_collection)
    svc.repo.create(_message("Unread"))
    svc.repo.create(_message("Read", read=True))
    unread = svc.list_all(unread_only=True)
    assert [m.data.name for m in unread] == ["Unread"]


def test_mark_read_and_replied(db: Client, clean_collection: str) -> None:
    svc = _service(db, clean_collection)
    record = svc.repo.create(_message("A"))
    assert record.data.read is False

    read = svc.mark_read(record.id)
    assert read.data.read is True

    replied = svc.mark_replied(record.id)
    assert replied.data.replied is True
    assert replied.data.read is True  # the earlier update wasn't clobbered


def test_export_csv_includes_a_header_and_every_message(db: Client, clean_collection: str) -> None:
    svc = _service(db, clean_collection)
    svc.repo.create(_message("A Visitor", message="Loved the write-up."))

    csv_text = svc.export_csv()
    lines = csv_text.strip().splitlines()
    assert lines[0].startswith("name,email,subject,message")
    assert "A Visitor" in csv_text
    assert "Loved the write-up." in csv_text


def test_delete_removes_the_message(db: Client, clean_collection: str) -> None:
    svc = _service(db, clean_collection)
    record = svc.repo.create(_message("A"))
    svc.delete(record.id)
    assert svc.repo.get(record.id) is None


def test_a_message_missing_created_at_still_appears(db: Client, clean_collection: str) -> None:
    """The regression this guards against: Firestore's .order_by("createdAt") silently
    excludes any document missing that field, so a message somehow created without one
    would vanish from the admin inbox with no error at all. list_all() must never drop a
    message purely because it can't be sorted precisely."""
    svc = _service(db, clean_collection)
    undated = ContactMessage.model_validate(
        {"name": "Undated", "email": "a@example.com", "message": "hi"}
    )
    svc.repo.create(undated)
    svc.repo.create(_message("Dated"))

    names = [m.data.name for m in svc.list_all()]
    assert "Undated" in names
    assert "Dated" in names

from __future__ import annotations

from google.cloud.firestore_v1 import Client

from kernel.records import Record
from kernel.security import Actor
from kernel.timestamps import now_iso, to_firestore
from shared.generated import ContactMessage
from src.inbox.messages.repository import MessageRepository
from src.inbox.messages.service import MessageService, csv_safe

ACTOR = Actor(uid="admin-1", email="admin@example.com")


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


def _seed(svc: MessageService, message: ContactMessage) -> Record[ContactMessage]:
    """Messages are created by inbox/contact; here they're written directly."""
    ref = svc.repo.db.collection(svc.repo.collection).document()
    ref.set(to_firestore(message.model_dump(mode="json", exclude_none=True)))
    return svc.repo.require(ref.id)


def test_list_all_returns_everything_by_default(db: Client, clean_collection: str) -> None:
    svc = _service(db, clean_collection)
    _seed(svc, _message("A"))
    _seed(svc, _message("B", read=True))
    assert len(svc.list_all()) == 2


def test_list_all_can_filter_to_unread(db: Client, clean_collection: str) -> None:
    svc = _service(db, clean_collection)
    _seed(svc, _message("Unread"))
    _seed(svc, _message("Read", read=True))
    unread = svc.list_all(unread_only=True)
    assert [m.data.name for m in unread] == ["Unread"]


def test_mark_read_and_replied(db: Client, clean_collection: str) -> None:
    svc = _service(db, clean_collection)
    record = _seed(svc, _message("A"))
    assert record.data.read is False

    read = svc.mark_read(record.id, ACTOR)
    assert read.data.read is True

    replied = svc.mark_replied(record.id, ACTOR)
    assert replied.data.replied is True
    assert replied.data.read is True  # the earlier update wasn't clobbered


def test_export_csv_includes_a_header_and_every_message(db: Client, clean_collection: str) -> None:
    svc = _service(db, clean_collection)
    _seed(svc, _message("A Visitor", message="Loved the write-up."))

    csv_text = svc.export_csv()
    lines = csv_text.strip().splitlines()
    assert lines[0].startswith("name,email,subject,message")
    assert "A Visitor" in csv_text
    assert "Loved the write-up." in csv_text


def test_delete_removes_the_message(db: Client, clean_collection: str) -> None:
    svc = _service(db, clean_collection)
    record = _seed(svc, _message("A"))
    svc.delete(record.id, ACTOR)
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
    _seed(svc, undated)
    _seed(svc, _message("Dated"))

    names = [m.data.name for m in svc.list_all()]
    assert "Undated" in names
    assert "Dated" in names


def test_csv_cells_cannot_become_spreadsheet_formulas() -> None:
    formula = '=HYPERLINK("https://evil.example","click")'
    assert csv_safe(formula) == "'" + formula
    assert csv_safe("+1 555") == "'+1 555"
    assert csv_safe("plain text") == "plain text"
    assert csv_safe(0.5) == 0.5

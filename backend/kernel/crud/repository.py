"""BaseRepository[T] — Firestore CRUD for one visibility/order collection.

Repositories are the only code that imports the Firestore SDK (kernel/firebase.py just
constructs the client). That keeps services testable without an emulator.

A subdomain's repository subclasses it:

    class SkillRepository(BaseRepository[Skill]):
        collection = "skills"
        model = Skill

Each subdomain declares its own (see src/content/skills/repository.py).
"""

from __future__ import annotations

from google.cloud.firestore_v1 import Client, CollectionReference, Query
from google.cloud.firestore_v1.base_query import FieldFilter
from pydantic import BaseModel

from kernel.errors import NotFoundError
from kernel.firebase import get_db
from kernel.records import Record
from kernel.timestamps import from_firestore, to_firestore


class BaseRepository[T: BaseModel]:
    collection: str
    model: type[T]

    def __init__(self, db: Client | None = None) -> None:
        self._db = db if db is not None else get_db()

    @property
    def db(self) -> Client:
        return self._db

    @property
    def _ref(self) -> CollectionReference:
        return self._db.collection(self.collection)

    # ── reads ────────────────────────────────────────────────────────

    def get(self, doc_id: str) -> Record[T] | None:
        snap = self._ref.document(doc_id).get()
        if not snap.exists:
            return None
        return self._to_record(doc_id, snap.to_dict() or {})

    def require(self, doc_id: str) -> Record[T]:
        record = self.get(doc_id)
        if record is None:
            raise NotFoundError(f"{self.model.__name__} '{doc_id}' not found.")
        return record

    def list_all(
        self, *, visibility: str | None = None, order_by: str | None = "order"
    ) -> list[Record[T]]:
        """Small collections (skills, experience, contact_messages) that the admin panel
        always loads whole.

        `order_by=None` skips server-side ordering entirely. Firestore's `.order_by(field)`
        silently *excludes* any document where that field is absent — fine for `order`,
        which every content schema defaults to 0 so it is always written, but wrong for a
        collection like contact_messages where nothing guarantees every document has the
        field (a partial migration, a manually-corrected record). An admin inbox silently
        losing a message because of one bad `.order_by()` is a worse failure than a message
        that just doesn't sort quite right — pass `order_by=None` and sort client-side with
        a null-safe key when that guarantee matters more than server-side ordering.
        """
        query: Query | CollectionReference = self._ref
        if visibility is not None:
            query = query.where(filter=FieldFilter("visibility", "==", visibility))
        if order_by is not None:
            query = query.order_by(order_by)
        return [self._to_record(s.id, s.to_dict() or {}) for s in query.stream()]

    # ── writes ───────────────────────────────────────────────────────

    def exists(self, doc_id: str) -> bool:
        return bool(self._ref.document(doc_id).get().exists)

    def create(self, data: T, *, doc_id: str | None = None) -> Record[T]:
        ref = self._ref.document(doc_id) if doc_id else self._ref.document()
        ref.set(self._payload(data))
        return self.require(ref.id)

    def save(self, doc_id: str, data: T) -> Record[T]:
        """Full replace (upsert) of the document at `doc_id`."""
        self._ref.document(doc_id).set(self._payload(data))
        return self.require(doc_id)

    def update(self, doc_id: str, patch: dict[str, object]) -> Record[T]:
        """Partial update. `patch` uses dotted paths for nested fields, same as Firestore's
        own `update()` — the caller is responsible for only including fields that changed."""
        self.require(doc_id)  # 404s before writing, rather than silently upserting
        self._ref.document(doc_id).update(to_firestore(dict(patch)))
        return self.require(doc_id)

    def delete(self, doc_id: str) -> None:
        self.require(doc_id)
        self._ref.document(doc_id).delete()

    def reorder(self, ordered_ids: list[str]) -> None:
        """Assign `order` = 0..n-1 following the given id sequence, in one batch."""
        batch = self._db.batch()
        for index, doc_id in enumerate(ordered_ids):
            batch.update(self._ref.document(doc_id), {"order": index})
        batch.commit()

    # ── internal ─────────────────────────────────────────────────────

    @staticmethod
    def _payload(data: T) -> dict[str, object]:
        return to_firestore(data.model_dump(mode="json", exclude_none=True))

    def _to_record(self, doc_id: str, raw: dict[str, object]) -> Record[T]:
        converted = from_firestore(raw)
        return Record(id=doc_id, data=self.model.model_validate(converted))


__all__ = ["BaseRepository", "Record"]

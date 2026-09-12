"""BaseRepository[T] — generic Firestore CRUD.

This is the only code allowed to import the Firestore SDK (besides shared/core/firebase.py,
which just constructs the client). That is what keeps services testable without an
emulator, and what would make swapping the database a bounded task.

Subclassing is meant to be nearly free:

    class SkillRepository(BaseRepository[Skill]):
        collection = "skills"
        model = Skill

Most content domains need nothing more than that plus a service that calls it.
"""

from __future__ import annotations

from dataclasses import dataclass

from google.cloud.firestore_v1 import Client, CollectionReference, Query
from google.cloud.firestore_v1.base_query import FieldFilter
from pydantic import BaseModel

from shared.core.errors import NotFoundError
from shared.core.firebase import get_db
from shared.core.timestamps import from_firestore, now_iso, to_firestore


@dataclass(frozen=True, slots=True)
class Record[T]:
    """A model plus the Firestore document id it lives at.

    The generated schemas never carry an `id` field — every one of them sets
    additionalProperties to false, so injecting one would fail validation. The id travels
    alongside the model instead.
    """

    id: str
    data: T


@dataclass(frozen=True, slots=True)
class Page[T]:
    items: list[Record[T]]
    next_cursor: str | None


class BaseRepository[T: BaseModel]:
    collection: str
    model: type[T]

    def __init__(self, db: Client | None = None) -> None:
        self._db = db if db is not None else get_db()

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

    def find_one(self, field: str, value: object) -> Record[T] | None:
        """A single-field equality lookup — e.g. a project by slug when the caller does
        not already know the document id (slug-keyed collections use slug AS the id, so
        this is mostly for the exceptional case)."""
        query = self._ref.where(filter=FieldFilter(field, "==", value)).limit(1)
        for snap in query.stream():
            return self._to_record(snap.id, snap.to_dict() or {})
        return None

    def list_page(
        self,
        *,
        visibility: str | None = None,
        order_by: str = "order",
        limit: int = 50,
        cursor: str | None = None,
    ) -> Page[T]:
        """Paginated list, filtered by visibility and sorted by `order_by`.

        The cursor is the last-seen document id from a previous page. Firestore's
        start_after needs a document *snapshot*, so the cursor id is re-fetched — one
        extra read per page, which is a fine trade for cursors that stay valid even if
        earlier documents are deleted (an offset-based cursor would not).
        """
        query: Query | CollectionReference = self._ref
        if visibility is not None:
            query = query.where(filter=FieldFilter("visibility", "==", visibility))
        query = query.order_by(order_by).order_by("__name__").limit(limit + 1)

        if cursor:
            cursor_snap = self._ref.document(cursor).get()
            if cursor_snap.exists:
                query = query.start_after(cursor_snap)

        snaps = list(query.stream())
        has_more = len(snaps) > limit
        snaps = snaps[:limit]

        items = [self._to_record(s.id, s.to_dict() or {}) for s in snaps]
        next_cursor = snaps[-1].id if has_more and snaps else None
        return Page(items=items, next_cursor=next_cursor)

    def list_all(
        self, *, visibility: str | None = None, order_by: str = "order"
    ) -> list[Record[T]]:
        """Small collections (skills, experience) that the admin panel always loads whole."""
        query: Query | CollectionReference = self._ref
        if visibility is not None:
            query = query.where(filter=FieldFilter("visibility", "==", visibility))
        query = query.order_by(order_by)
        return [self._to_record(s.id, s.to_dict() or {}) for s in query.stream()]

    # ── writes ───────────────────────────────────────────────────────

    def create(self, data: T, *, doc_id: str | None = None) -> Record[T]:
        payload = data.model_dump(mode="json", exclude_none=True)
        payload = to_firestore(payload)

        if doc_id:
            ref = self._ref.document(doc_id)
            ref.set(payload)
            new_id = doc_id
        else:
            ref = self._ref.document()
            ref.set(payload)
            new_id = ref.id

        return self.require(new_id)

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

    def _to_record(self, doc_id: str, raw: dict[str, object]) -> Record[T]:
        converted = from_firestore(raw)
        return Record(id=doc_id, data=self.model.model_validate(converted))


__all__ = ["BaseRepository", "Page", "Record", "now_iso"]

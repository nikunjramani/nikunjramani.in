"""media_assets — what the library needs: list, read, update alt text, delete — plus the
one cross-collection read the library owns: which content documents still mention an
asset. (media/processing has its own repository for creating new assets.)"""

from __future__ import annotations

from google.cloud.firestore_v1 import Client, CollectionReference

from kernel.audit import AuditEntry, stage
from kernel.errors import NotFoundError
from kernel.firebase import get_db
from kernel.records import Record
from kernel.timestamps import from_firestore, to_firestore
from shared.generated import MediaAsset

COLLECTION = "media_assets"

# Every content collection an asset's URL can appear in. Scanned by name, not by importing
# the content domain (ADR 0017); tests/test_domain_registry.py keeps it equal to the
# schemas' publicRead collections.
CONTENT_COLLECTIONS: tuple[str, ...] = (
    "profile",
    "projects",
    "skills",
    "experience",
    "education",
    "certifications",
    "posts",
    "site_config",
)


class LibraryRepository:
    collection = COLLECTION
    content_collections = CONTENT_COLLECTIONS

    def __init__(self, db: Client | None = None) -> None:
        self._db = db if db is not None else get_db()

    @property
    def db(self) -> Client:
        return self._db

    @property
    def _ref(self) -> CollectionReference:
        return self._db.collection(self.collection)

    def get(self, asset_id: str) -> Record[MediaAsset] | None:
        snap = self._ref.document(asset_id).get()
        return self._record(asset_id, snap.to_dict() or {}) if snap.exists else None

    def require(self, asset_id: str) -> Record[MediaAsset]:
        record = self.get(asset_id)
        if record is None:
            raise NotFoundError(f"Media asset '{asset_id}' not found.")
        return record

    def list_newest_last(self) -> list[Record[MediaAsset]]:
        query = self._ref.order_by("uploadedAt")
        return [self._record(s.id, s.to_dict() or {}) for s in query.stream()]

    # Writes commit with their audit entry, in one batch (kernel/audit.py).

    def save(
        self, asset_id: str, asset: MediaAsset, *, audit: AuditEntry | None = None
    ) -> Record[MediaAsset]:
        batch = self._db.batch()
        batch.set(self._ref.document(asset_id), self._payload(asset))
        stage(self._db, batch, audit)
        batch.commit()
        return self.require(asset_id)

    def delete(self, asset_id: str, *, audit: AuditEntry | None = None) -> None:
        self.require(asset_id)
        batch = self._db.batch()
        batch.delete(self._ref.document(asset_id))
        stage(self._db, batch, audit)
        batch.commit()

    def find_references(self, urls: set[str]) -> list[str]:
        """`collection/id` of every content document — drafts included — that mentions any
        of `urls` anywhere in its data. A full scan: fine at tens of documents, and it can't
        drift the way a maintained reference count would."""
        return [
            f"{collection}/{snap.id}"
            for collection in self.content_collections
            for snap in self._db.collection(collection).stream()
            if _mentions(snap.to_dict() or {}, urls)
        ]

    @staticmethod
    def _payload(asset: MediaAsset) -> dict[str, object]:
        return to_firestore(asset.model_dump(mode="json", exclude_none=True))

    @staticmethod
    def _record(asset_id: str, raw: dict[str, object]) -> Record[MediaAsset]:
        return Record(id=asset_id, data=MediaAsset.model_validate(from_firestore(raw)))


def _mentions(value: object, urls: set[str]) -> bool:
    if isinstance(value, str):
        return value in urls
    if isinstance(value, list):
        return any(_mentions(v, urls) for v in value)
    if isinstance(value, dict):
        return any(_mentions(v, urls) for v in value.values())
    return False

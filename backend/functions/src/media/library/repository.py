"""media_assets — what the library needs: list, read, update alt text, delete.
(media/processing has its own repository for creating new assets.)"""

from __future__ import annotations

from google.cloud.firestore_v1 import Client, CollectionReference

from kernel.errors import NotFoundError
from kernel.firebase import get_db
from kernel.records import Record
from kernel.timestamps import from_firestore, to_firestore
from shared.generated import MediaAsset

COLLECTION = "media_assets"


class LibraryRepository:
    collection = COLLECTION

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

    def save(self, asset_id: str, asset: MediaAsset) -> Record[MediaAsset]:
        self._ref.document(asset_id).set(self._payload(asset))
        return self.require(asset_id)

    def delete(self, asset_id: str) -> None:
        self.require(asset_id)
        self._ref.document(asset_id).delete()

    @staticmethod
    def _payload(asset: MediaAsset) -> dict[str, object]:
        return to_firestore(asset.model_dump(mode="json", exclude_none=True))

    @staticmethod
    def _record(asset_id: str, raw: dict[str, object]) -> Record[MediaAsset]:
        return Record(id=asset_id, data=MediaAsset.model_validate(from_firestore(raw)))

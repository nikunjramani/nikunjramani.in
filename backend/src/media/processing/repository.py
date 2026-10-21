"""media_assets — what processing needs: record a new asset, and know if it already was."""

from __future__ import annotations

from google.cloud.firestore_v1 import Client

from kernel.firebase import get_db
from kernel.timestamps import to_firestore
from shared.generated import MediaAsset


class NewAssetRepository:
    collection = "media_assets"

    def __init__(self, db: Client | None = None) -> None:
        self._db = db if db is not None else get_db()

    def exists(self, asset_id: str) -> bool:
        return bool(self._db.collection(self.collection).document(asset_id).get().exists)

    def create(self, asset_id: str, asset: MediaAsset) -> None:
        payload = to_firestore(asset.model_dump(mode="json", exclude_none=True))
        self._db.collection(self.collection).document(asset_id).set(payload)

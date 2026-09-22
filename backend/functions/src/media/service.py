"""Media doesn't fit shared/crud.py's generic shape: creation happens inside the
on_media_uploaded trigger (once the actual bytes are known), not through a POST body, and
there's no visibility/publish concept — an asset just exists or doesn't. See
docs/plan/phases/phase-3-backend.md gotchas and ADR 0012 for why this stays hand-written."""

from __future__ import annotations

import contextlib

from google.cloud.firestore_v1 import Client

from shared.core.errors import NotFoundError
from shared.core.timestamps import now_iso
from shared.generated import MediaAsset
from shared.repositories.base import Record
from shared.services.storage import StorageService, new_object_path, validate_upload
from src.media.repository import MediaRepository


class MediaService:
    def __init__(
        self,
        db: Client | None = None,
        *,
        repo: MediaRepository | None = None,
        storage: StorageService | None = None,
    ) -> None:
        self.repo = repo if repo is not None else MediaRepository(db)
        self._storage = storage if storage is not None else StorageService()

    def request_upload(self, *, content_type: str, size_bytes: int) -> dict[str, str]:
        validate_upload(content_type, size_bytes)
        path = new_object_path(content_type)
        upload_url = self._storage.create_signed_upload_url(path=path, content_type=content_type)
        return {"uploadUrl": upload_url, "path": path}

    def list_all(self) -> list[Record[MediaAsset]]:
        return self.repo.list_all(order_by="uploadedAt")

    def get(self, doc_id: str) -> Record[MediaAsset]:
        return self.repo.require(doc_id)

    def create_from_processed_upload(
        self,
        *,
        original_path: str,
        url: str,
        thumbnail_url: str,
        width: int,
        height: int,
        blurhash: str,
        content_type: str,
        size_bytes: int,
        uploaded_by: str | None,
    ) -> Record[MediaAsset]:
        asset = MediaAsset(
            url=url,  # type: ignore[arg-type]
            path=original_path,
            type="image",  # type: ignore[arg-type]
            contentType=content_type,
            sizeBytes=size_bytes,
            width=width,
            height=height,
            blurhash=blurhash,
            thumbnailUrl=thumbnail_url,  # type: ignore[arg-type]
            usageCount=0,
            uploadedBy=uploaded_by,
            uploadedAt=now_iso(),  # type: ignore[arg-type]
        )
        return self.repo.create(asset)

    def delete(self, doc_id: str) -> None:
        asset = self.repo.get(doc_id)
        if asset is None:
            raise NotFoundError(f"Media asset '{doc_id}' not found.")
        # Best-effort: if the Storage delete fails partway, the Firestore record is gone
        # too rather than left dangling and pointing at nothing — an orphaned Storage blob
        # costs a few KB; an admin panel entry pointing at a 404'd image is worse.
        with contextlib.suppress(Exception):
            self._storage.delete(asset.data.path)
        self.repo.delete(doc_id)

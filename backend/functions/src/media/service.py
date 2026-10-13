"""Media doesn't fit shared/crud.py's generic shape: creation happens inside the
on_media_uploaded trigger (once the actual bytes are known), not through a POST body, and
there's no visibility/publish concept — an asset just exists or doesn't. See ADR 0012."""

from __future__ import annotations

import contextlib

from google.cloud.firestore_v1 import Client

from shared.core.timestamps import now_iso
from shared.crud import actor_of
from shared.generated import MediaAsset
from shared.repositories.base import Record
from shared.repositories.references import ReferenceRepository
from shared.services.audit import Action, AuditService
from shared.services.storage import ALLOWED_CONTENT_TYPES, StorageService, validate_upload
from src.media.paths import asset_id_of, new_upload_path, processed_path, thumbnail_path
from src.media.repository import MediaRepository


class MediaService:
    def __init__(
        self,
        db: Client | None = None,
        *,
        repo: MediaRepository | None = None,
        storage: StorageService | None = None,
        audit: AuditService | None = None,
        references: ReferenceRepository | None = None,
    ) -> None:
        self.repo = repo if repo is not None else MediaRepository(db)
        self._storage = storage if storage is not None else StorageService()
        self._audit = audit if audit is not None else AuditService(self.repo.db)
        self._references = (
            references if references is not None else ReferenceRepository(self.repo.db)
        )

    def request_upload(self, *, content_type: str, size_bytes: int) -> dict[str, str]:
        validate_upload(content_type, size_bytes)
        path = new_upload_path(ALLOWED_CONTENT_TYPES[content_type])
        upload_url = self._storage.create_signed_upload_url(path=path, content_type=content_type)
        return {"uploadUrl": upload_url, "path": path}

    def list_all(self) -> list[Record[MediaAsset]]:
        return self.repo.list_all(order_by="uploadedAt")

    def get(self, doc_id: str) -> Record[MediaAsset]:
        return self.repo.require(doc_id)

    def usage(self, doc_id: str) -> list[str]:
        """`collection/id` of every content document still pointing at this asset."""
        asset = self.repo.require(doc_id).data
        urls = {str(asset.url)}
        if asset.thumbnailUrl:
            urls.add(str(asset.thumbnailUrl))
        return self._references.documents_mentioning(urls)

    def create_from_processed_upload(
        self,
        *,
        asset_id: str,
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
            uploadedBy=uploaded_by,
            uploadedAt=now_iso(),  # type: ignore[arg-type]
        )
        return self.repo.create(asset, doc_id=asset_id)

    def update_metadata(
        self, doc_id: str, *, alt: str, caption: str | None, claims: dict[str, object]
    ) -> Record[MediaAsset]:
        """Alt text has to be editable after upload — there's no alt at the moment a file
        lands in Storage. The admin panel refuses to let an asset without one be used."""
        existing = self.repo.require(doc_id)
        updated = existing.data.model_copy(update={"alt": alt, "caption": caption})
        record = self.repo.save(doc_id, updated)
        self._record("update", doc_id, claims, before=existing.data, after=record.data)
        return record

    def delete(self, doc_id: str, claims: dict[str, object]) -> None:
        asset = self.repo.require(doc_id)
        # Best-effort: an already-missing Storage object must not leave a Firestore record
        # pointing at nothing — an orphaned blob costs a few KB, a dangling entry is worse.
        asset_id = asset_id_of(asset.data.path)
        for path in (asset.data.path, processed_path(asset_id), thumbnail_path(asset_id)):
            with contextlib.suppress(Exception):
                self._storage.delete(path)
        self.repo.delete(doc_id)
        self._record("delete", doc_id, claims, before=asset.data, after=None)

    def _record(
        self,
        action: Action,
        doc_id: str,
        claims: dict[str, object],
        *,
        before: MediaAsset | None,
        after: MediaAsset | None,
    ) -> None:
        uid, email = actor_of(claims)
        self._audit.record(
            actor=uid,
            actor_email=email,
            action=action,
            collection=self.repo.collection,
            doc_id=doc_id,
            before=before.model_dump(mode="json", exclude_none=True) if before else None,
            after=after.model_dump(mode="json", exclude_none=True) if after else None,
        )

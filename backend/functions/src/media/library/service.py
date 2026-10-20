"""The admin media library. Assets are created by the processing trigger, never here.

"Where is this image used?" is answered here too, and delete enforces it: an asset still
referenced by a content document is only deleted with `force` — the admin has seen the
list and confirmed. The check lives in the API, not just the UI (ADR 0022)."""

from __future__ import annotations

import contextlib

from kernel.audit import Action, AuditWriter
from kernel.errors import ConflictError
from kernel.records import Record
from shared.generated import MediaAsset
from src.media.library.paths import asset_id_of, processed_path, thumbnail_path
from src.media.library.repository import LibraryRepository
from src.media.library.storage import LibraryStorage


class LibraryService:
    def __init__(
        self,
        repo: LibraryRepository | None = None,
        storage: LibraryStorage | None = None,
        audit: AuditWriter | None = None,
    ) -> None:
        self.repo = repo if repo is not None else LibraryRepository()
        self._storage = storage if storage is not None else LibraryStorage()
        self._audit = audit if audit is not None else AuditWriter(self.repo.db)

    def list_all(self) -> list[Record[MediaAsset]]:
        return self.repo.list_newest_last()

    def get(self, asset_id: str) -> Record[MediaAsset]:
        return self.repo.require(asset_id)

    def update_metadata(
        self, asset_id: str, *, alt: str, caption: str | None, claims: dict[str, object]
    ) -> Record[MediaAsset]:
        """Alt text is set after upload — there is none when a file lands in Storage. The
        admin panel refuses to let an asset without one be picked for use."""
        existing = self.repo.require(asset_id)
        updated = existing.data.model_copy(update={"alt": alt, "caption": caption})
        record = self.repo.save(asset_id, updated)
        self._record("update", asset_id, claims, before=existing.data, after=record.data)
        return record

    def usage(self, asset_id: str) -> list[str]:
        """`collection/id` of every content document still pointing at this asset."""
        return self._references(self.repo.require(asset_id))

    def delete(self, asset_id: str, claims: dict[str, object], *, force: bool = False) -> None:
        asset = self.repo.require(asset_id)
        if not force and (references := self._references(asset)):
            raise ConflictError(f"Still used by {', '.join(references)}.")
        # Best-effort: an already-missing blob must not leave a document pointing at
        # nothing — an orphaned blob costs a few KB, a dangling entry is worse.
        folder_id = asset_id_of(asset.data.path)
        for path in (asset.data.path, processed_path(folder_id), thumbnail_path(folder_id)):
            with contextlib.suppress(Exception):
                self._storage.delete(path)
        self.repo.delete(asset_id)
        self._record("delete", asset_id, claims, before=asset.data, after=None)

    def _references(self, asset: Record[MediaAsset]) -> list[str]:
        urls = {str(u) for u in (asset.data.url, asset.data.thumbnailUrl) if u is not None}
        return self.repo.find_references(urls)

    def _record(
        self,
        action: Action,
        asset_id: str,
        claims: dict[str, object],
        *,
        before: MediaAsset | None,
        after: MediaAsset | None,
    ) -> None:
        self._audit.record(
            claims=claims,
            action=action,
            collection=self.repo.collection,
            doc_id=asset_id,
            before=before.model_dump(mode="json", exclude_none=True) if before else None,
            after=after.model_dump(mode="json", exclude_none=True) if after else None,
        )

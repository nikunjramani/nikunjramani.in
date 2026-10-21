"""Raw upload → public WebP derivatives + a media_assets document.

Only `uploads/media/<id>/original.<ext>` is new work; everything written here lands under
public/ with other filenames, so the trigger never re-fires on its own output. Storage
events are at-least-once: a redelivered event finds the asset recorded and stops.
"""

from __future__ import annotations

from PIL import UnidentifiedImageError

from kernel.logging import get_logger
from kernel.timestamps import now_iso
from shared.generated import MediaAsset
from src.media.processing.image import process_image
from src.media.processing.paths import UPLOAD_PATTERN, processed_path, thumbnail_path
from src.media.processing.repository import NewAssetRepository
from src.media.processing.storage import ProcessingStorage

log = get_logger(__name__)


class ProcessingService:
    def __init__(
        self,
        repo: NewAssetRepository | None = None,
        storage: ProcessingStorage | None = None,
    ) -> None:
        self._repo = repo if repo is not None else NewAssetRepository()
        self._storage = storage if storage is not None else ProcessingStorage()

    def handle_upload(self, object_name: str, *, uploaded_by: str | None) -> str | None:
        """Process one finalized object; returns the new asset id, or None when it isn't new
        work or was already done."""
        match = UPLOAD_PATTERN.match(object_name)
        if not match:
            return None  # not a raw upload — including our own derivatives
        asset_id = match.group("id")
        if self._repo.exists(asset_id):
            log.info("media already processed", extra={"extra_fields": {"id": asset_id}})
            return None

        try:
            processed = process_image(self._storage.download_bytes(object_name))
        except UnidentifiedImageError:
            # Not a decodable image: no asset, and nothing to retry — a redelivery would fail
            # the same way (Eventarc retries any error for up to a day).
            log.error("upload is not an image", extra={"extra_fields": {"id": asset_id}})
            return None
        self._storage.upload_bytes(
            processed_path(asset_id), processed.original_webp, content_type="image/webp"
        )
        self._storage.upload_bytes(
            thumbnail_path(asset_id), processed.thumbnail_webp, content_type="image/webp"
        )
        asset = MediaAsset(
            url=self._storage.public_url(processed_path(asset_id)),  # type: ignore[arg-type]
            path=object_name,
            type="image",  # type: ignore[arg-type]
            contentType="image/webp",
            sizeBytes=len(processed.original_webp),
            width=processed.width,
            height=processed.height,
            blurhash=processed.blurhash,
            thumbnailUrl=self._storage.public_url(thumbnail_path(asset_id)),  # type: ignore[arg-type]
            uploadedBy=uploaded_by,
            uploadedAt=now_iso(),  # type: ignore[arg-type]
        )
        self._repo.create(asset_id, asset)
        log.info("media processed", extra={"extra_fields": {"id": asset_id}})
        return asset_id

"""on_media_uploaded — fires on every object finalized in the media bucket, so the first
thing it does is decide whether to act at all.

Only `uploads/media/<id>/original.<ext>` is new work. Everything this trigger writes lands
under public/ with a different filename, so its own output can never re-trigger it.
Storage events are at-least-once: a redelivered event finds the asset already recorded
and stops, instead of creating a duplicate library entry.
"""

from __future__ import annotations

from firebase_functions import storage_fn
from firebase_functions.core import CloudEvent

from shared.core.config import get_settings
from shared.core.logging import get_logger
from shared.services.image import process_image
from shared.services.storage import StorageService
from src.media.paths import UPLOAD_PATTERN, processed_path, thumbnail_path
from src.media.service import MediaService

log = get_logger(__name__)

# Must be a real string at decoration time — the decorator raises on import without it.
_MEDIA_BUCKET = get_settings().storage_bucket


@storage_fn.on_object_finalized(
    bucket=_MEDIA_BUCKET, region="asia-south1", memory=1024, max_instances=2
)
def on_media_uploaded(event: CloudEvent[storage_fn.StorageObjectData]) -> None:
    match = UPLOAD_PATTERN.match(event.data.name)
    if not match:
        return  # not a new upload — including our own processed/thumbnail output
    asset_id = match.group("id")

    storage = StorageService()
    media = MediaService(storage=storage)
    if media.repo.exists(asset_id):
        log.info("media already processed", extra={"extra_fields": {"id": asset_id}})
        return

    processed = process_image(storage.download_bytes(event.data.name))
    storage.upload_bytes(
        processed_path(asset_id), processed.original_webp, content_type="image/webp"
    )
    storage.upload_bytes(
        thumbnail_path(asset_id), processed.thumbnail_webp, content_type="image/webp"
    )

    media.create_from_processed_upload(
        asset_id=asset_id,
        original_path=event.data.name,
        url=storage.public_url(processed_path(asset_id)),
        thumbnail_url=storage.public_url(thumbnail_path(asset_id)),
        width=processed.width,
        height=processed.height,
        blurhash=processed.blurhash,
        content_type="image/webp",
        size_bytes=len(processed.original_webp),
        uploaded_by=(event.data.metadata or {}).get("uploadedBy"),
    )
    log.info("media processed", extra={"extra_fields": {"id": asset_id}})

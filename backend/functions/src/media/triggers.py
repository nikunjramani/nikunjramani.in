"""on_media_uploaded — fires on every object finalized in Storage, not just uploads this
domain cares about, so the very first thing it does is decide whether to act at all.

That filter is load-bearing, not a nice-to-have: this trigger's own output (the processed
WebP and thumbnail) lands in the same bucket the trigger watches. Writing output that also
matched the trigger's input pattern would reprocess its own output forever. The convention
that makes this safe: only `.../original.<ext>` is ever treated as new work; everything
this trigger itself writes uses a different filename (`processed.webp`, `thumbnail.webp`)
that can never match.
"""

from __future__ import annotations

import re

from firebase_functions import storage_fn
from firebase_functions.core import CloudEvent

from shared.core.config import get_settings
from shared.core.logging import get_logger
from shared.services.image import process_image
from shared.services.storage import StorageService
from src.media.service import MediaService

log = get_logger(__name__)

_ORIGINAL_PATTERN = re.compile(r"^public/media/[^/]+/original\.[a-z0-9]+$")

# The bucket to watch must be a real string at *decoration* time — this line runs on
# import, not on first invocation, and the decorator raises immediately if it's missing
# (caught by trying to import main.py locally, which is exactly why that's worth doing).
_MEDIA_BUCKET = get_settings().storage_bucket


@storage_fn.on_object_finalized(bucket=_MEDIA_BUCKET, region="asia-south1", memory=1024)
def on_media_uploaded(event: CloudEvent[storage_fn.StorageObjectData]) -> None:
    data = event.data
    if not _ORIGINAL_PATTERN.match(data.name):
        return  # not a new upload we own — including our own processed/thumbnail output

    storage = StorageService()
    raw = storage.download_bytes(data.name)
    processed = process_image(raw)

    folder = data.name.rsplit("/", 1)[0]
    processed_path = f"{folder}/processed.webp"
    thumbnail_path = f"{folder}/thumbnail.webp"

    storage.upload_bytes(processed_path, processed.original_webp, content_type="image/webp")
    storage.upload_bytes(thumbnail_path, processed.thumbnail_webp, content_type="image/webp")

    MediaService(storage=storage).create_from_processed_upload(
        original_path=data.name,
        url=storage.public_url(processed_path),
        thumbnail_url=storage.public_url(thumbnail_path),
        width=processed.width,
        height=processed.height,
        blurhash=processed.blurhash,
        content_type="image/webp",
        size_bytes=len(processed.original_webp),
        uploaded_by=(data.metadata or {}).get("uploadedBy"),
    )
    log.info("media processed", extra={"extra_fields": {"path": data.name}})

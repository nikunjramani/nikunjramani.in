"""The media bucket's object layout — the one place it's spelled out.

    uploads/media/<id>/original.<ext>   the raw upload: private (storage.rules default-deny,
                                        and outside the public/ managed folder), may carry
                                        EXIF such as GPS location
    public/media/<id>/processed.webp    world-readable derivatives written by the trigger —
    public/media/<id>/thumbnail.webp    re-encoded by Pillow, so no EXIF survives

<id> is also the media_assets document id, which makes trigger redelivery idempotent.
Assets created before this layout have `path` = public/media/<id>/original.<ext>; every
helper here accepts both.
"""

from __future__ import annotations

import re
import uuid

UPLOAD_PATTERN = re.compile(r"^uploads/media/(?P<id>[0-9a-f]{32})/original\.[a-z0-9]+$")


def new_upload_path(extension: str) -> str:
    return f"uploads/media/{uuid.uuid4().hex}/original.{extension}"


def asset_id_of(original_path: str) -> str:
    """The <id> segment of either layout's original path."""
    parts = original_path.split("/")
    if len(parts) != 4 or parts[1] != "media":
        raise ValueError(f"not a media object path: {original_path!r}")
    return parts[2]


def processed_path(asset_id: str) -> str:
    return f"public/media/{asset_id}/processed.webp"


def thumbnail_path(asset_id: str) -> str:
    return f"public/media/{asset_id}/thumbnail.webp"

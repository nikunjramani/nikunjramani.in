"""What counts as new work, and where derivatives go.

The media bucket's layout (also in backend/README.md):

    uploads/media/<id>/original.<ext>   raw upload — private, may carry EXIF/GPS
    public/media/<id>/processed.webp    world-readable derivatives, no EXIF
    public/media/<id>/thumbnail.webp

<id> is also the media_assets document id.

Only `uploads/media/<id>/original.<ext>` matches UPLOAD_PATTERN; everything this
subdomain writes is under public/ with other filenames, so it never re-triggers itself.
"""

import re

UPLOAD_PATTERN = re.compile(r"^uploads/media/(?P<id>[0-9a-f]{32})/original\.[a-z0-9]+$")


def processed_path(asset_id: str) -> str:
    return f"public/media/{asset_id}/processed.webp"


def thumbnail_path(asset_id: str) -> str:
    return f"public/media/{asset_id}/thumbnail.webp"

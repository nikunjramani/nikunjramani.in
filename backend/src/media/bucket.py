"""The media bucket — the one contract media's subdomains share (ADR 0024).

upload writes raw files into it, processing turns them into public derivatives, library
deletes them. All three must agree on its name and layout, so that agreement lives once,
here, rather than in three copies held together by a test. It holds the contract only — no
service, no repository, nothing a subdomain does with the bucket.

    uploads/media/<id>/original.<ext>   raw upload — private, may carry EXIF/GPS
    public/media/<id>/processed.webp    world-readable derivatives, no EXIF
    public/media/<id>/thumbnail.webp

<id> is also the media_assets document id. Only an upload path matches UPLOAD_PATTERN;
everything processing writes is under public/ with other filenames, so it never
re-triggers itself.
"""

from __future__ import annotations

import re
import uuid
from functools import lru_cache

from google.cloud.storage import Bucket
from google.cloud.storage import Client as StorageClient

from kernel.config import ServiceSettings

UPLOAD_PATTERN = re.compile(r"^uploads/media/(?P<id>[0-9a-f]{32})/original\.[a-z0-9]+$")


class MediaSettings(ServiceSettings):
    required_in_production = ("storage_bucket",)

    storage_bucket: str = "nikunjramani-in-media"


@lru_cache
def get_media_settings() -> MediaSettings:
    return MediaSettings()


@lru_cache
def storage_client() -> StorageClient:
    """One client per process — it holds an authorised HTTP session worth reusing."""
    return StorageClient()


def media_bucket(client: StorageClient | None = None) -> Bucket:
    client = client if client is not None else storage_client()
    return client.bucket(get_media_settings().storage_bucket)


def new_upload_path(extension: str) -> str:
    return f"uploads/media/{uuid.uuid4().hex}/original.{extension}"


def asset_id_of(original_path: str) -> str:
    """The asset id in an original's path. Assets created before uploads moved to uploads/
    have `path` = public/media/<id>/original.<ext>; this reads either layout."""
    parts = original_path.split("/")
    if len(parts) != 4 or parts[1] != "media":
        raise ValueError(f"not a media object path: {original_path!r}")
    return parts[2]


def processed_path(asset_id: str) -> str:
    return f"public/media/{asset_id}/processed.webp"


def thumbnail_path(asset_id: str) -> str:
    return f"public/media/{asset_id}/thumbnail.webp"


def public_url(path: str) -> str:
    return f"https://storage.googleapis.com/{get_media_settings().storage_bucket}/{path}"

"""media — entry point. Every Firebase function this domain deploys, mapped to the
subdomain `main` module that defines it. Nothing is imported here; see the root main.py."""

FUNCTIONS: dict[str, str] = {
    "api_media_upload": "src.media.upload.main",
    "api_media_library": "src.media.library.main",
    "on_media_uploaded": "src.media.processing.main",
}

"""media/upload — entry point: deploys api_media_upload (admin)."""

from kernel.http import make_function
from src.media.upload.routes import router

api_media_upload = make_function(router, name="api_media_upload", max_instances=2)

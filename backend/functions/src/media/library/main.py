"""media/library — entry point: deploys api_media_library (admin)."""

from kernel.http import make_function
from src.media.library.routes import router

api_media_library = make_function(router, name="api_media_library", max_instances=2)

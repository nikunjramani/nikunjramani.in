"""Media domain — exports api_media. See ADR 0011."""

from firebase_functions import options

from shared.api import make_function

from .routes import router

api_media = make_function(
    router, name="api_media", memory=options.MemoryOption.GB_1, max_instances=2
)

__all__ = ["api_media"]

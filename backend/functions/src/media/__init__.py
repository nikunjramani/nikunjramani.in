"""Media domain — exports api_media. See ADR 0011."""

from shared.api import make_function

from .routes import router

api_media = make_function(router, name="api_media")

__all__ = ["api_media"]

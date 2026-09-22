"""Settings domain — exports api_settings. See ADR 0011."""

from shared.api import make_function

from .routes import router

api_settings = make_function(router, name="api_settings")

__all__ = ["api_settings"]

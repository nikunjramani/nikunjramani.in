"""Profile domain — exports api_profile. See ADR 0011."""

from shared.api import make_function

from .routes import router

api_profile = make_function(router, name="api_profile")

__all__ = ["api_profile"]

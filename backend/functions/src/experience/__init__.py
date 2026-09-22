"""Experience domain — exports api_experience. See ADR 0011."""

from shared.api import make_function

from .routes import router

api_experience = make_function(router, name="api_experience")

__all__ = ["api_experience"]

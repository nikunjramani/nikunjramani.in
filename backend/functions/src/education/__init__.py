"""Education domain — exports api_education. See ADR 0011."""

from shared.api import make_function

from .routes import router

api_education = make_function(router, name="api_education")

__all__ = ["api_education"]

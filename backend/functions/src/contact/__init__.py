"""Contact domain — exports api_contact. See ADR 0011."""

from shared.api import make_function

from .routes import router

api_contact = make_function(router, name="api_contact")

__all__ = ["api_contact"]

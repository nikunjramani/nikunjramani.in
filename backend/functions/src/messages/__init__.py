"""Messages domain — exports api_messages. See ADR 0011."""

from shared.api import make_function

from .routes import router

api_messages = make_function(router, name="api_messages")

__all__ = ["api_messages"]

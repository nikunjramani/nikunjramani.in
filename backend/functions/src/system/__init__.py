"""System domain — exports api_system."""

from shared.api import make_function

from .routes import router

api_system = make_function(router, name="api_system")

__all__ = ["api_system"]

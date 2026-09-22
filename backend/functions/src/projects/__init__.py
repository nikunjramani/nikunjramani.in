"""Projects domain — exports api_projects. See ADR 0011."""

from shared.api import make_function

from .routes import router

api_projects = make_function(router, name="api_projects")

__all__ = ["api_projects"]

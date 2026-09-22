"""Post domain — exports api_posts. See ADR 0011."""

from shared.api import make_function

from .routes import router

api_posts = make_function(router, name="api_posts")

__all__ = ["api_posts"]

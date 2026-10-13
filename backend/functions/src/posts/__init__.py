"""Posts domain — exports api_posts. A standard content domain, built whole
from its model by shared.crud.content_domain (ADR 0016); deployed alone per ADR 0011."""

from shared.api import make_function
from shared.crud import content_domain
from shared.generated import Post

domain = content_domain(Post, collection="posts", slugged=True)
api_posts = make_function(domain.router, name="api_posts")

__all__ = ["api_posts", "domain"]

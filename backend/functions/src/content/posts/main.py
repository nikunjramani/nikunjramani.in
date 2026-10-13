"""content/posts — entry point: deploys api_content_posts (admin)."""

from kernel.http import make_function
from src.content.posts.routes import router

api_content_posts = make_function(router, name="api_content_posts")

"""content/profile — entry point: deploys api_content_profile (admin)."""

from kernel.http import make_function
from src.content.profile.routes import router

api_content_profile = make_function(router, name="api_content_profile")

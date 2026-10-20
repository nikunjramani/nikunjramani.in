"""content/settings — entry point: deploys api_content_settings (admin + public reads)."""

from kernel.http import make_function
from src.content.settings.routes import router

api_content_settings = make_function(router, name="api_content_settings")

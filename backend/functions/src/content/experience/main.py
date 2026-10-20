"""content/experience — entry point: deploys api_content_experience (admin + public reads)."""

from kernel.http import make_function
from src.content.experience.routes import router

api_content_experience = make_function(router, name="api_content_experience")

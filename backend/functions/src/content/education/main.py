"""content/education — entry point: deploys api_content_education (admin + public reads)."""

from kernel.http import make_function
from src.content.education.routes import router

api_content_education = make_function(router, name="api_content_education")

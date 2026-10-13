"""content/certifications — entry point: deploys api_content_certifications (admin)."""

from kernel.http import make_function
from src.content.certifications.routes import router

api_content_certifications = make_function(router, name="api_content_certifications")

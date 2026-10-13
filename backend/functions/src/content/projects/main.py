"""content/projects — entry point: deploys api_content_projects (admin)."""

from kernel.http import make_function
from src.content.projects.routes import router

api_content_projects = make_function(router, name="api_content_projects")

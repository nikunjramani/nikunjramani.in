"""content/skills — entry point: deploys api_content_skills (admin)."""

from kernel.http import make_function
from src.content.skills.routes import router

api_content_skills = make_function(router, name="api_content_skills")

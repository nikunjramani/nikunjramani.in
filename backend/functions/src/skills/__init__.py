"""Skill domain — exports api_skills. See ADR 0011."""

from shared.api import make_function

from .routes import router

api_skills = make_function(router, name="api_skills")

__all__ = ["api_skills"]

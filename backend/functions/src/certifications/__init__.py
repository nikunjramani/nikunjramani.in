"""Certification domain — exports api_certifications. See ADR 0011."""

from shared.api import make_function

from .routes import router

api_certifications = make_function(router, name="api_certifications")

__all__ = ["api_certifications"]

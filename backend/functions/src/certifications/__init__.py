"""Certifications domain — exports api_certifications. A standard content domain, built whole
from its model by shared.crud.content_domain (ADR 0016); deployed alone per ADR 0011."""

from shared.api import make_function
from shared.crud import content_domain
from shared.generated import Certification

domain = content_domain(Certification, collection="certifications")
api_certifications = make_function(domain.router, name="api_certifications")

__all__ = ["api_certifications", "domain"]

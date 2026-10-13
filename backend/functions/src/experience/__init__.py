"""Experience domain — exports api_experience. A standard content domain, built whole
from its model by shared.crud.content_domain (ADR 0016); deployed alone per ADR 0011."""

from shared.api import make_function
from shared.crud import content_domain
from shared.generated import Experience

domain = content_domain(Experience, collection="experience")
api_experience = make_function(domain.router, name="api_experience")

__all__ = ["api_experience", "domain"]

"""Skills domain — exports api_skills. A standard content domain, built whole
from its model by shared.crud.content_domain (ADR 0016); deployed alone per ADR 0011."""

from shared.api import make_function
from shared.crud import content_domain
from shared.generated import Skill

domain = content_domain(Skill, collection="skills")
api_skills = make_function(domain.router, name="api_skills")

__all__ = ["api_skills", "domain"]

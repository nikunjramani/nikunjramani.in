"""Education domain — exports api_education. A standard content domain, built whole
from its model by shared.crud.content_domain (ADR 0016); deployed alone per ADR 0011."""

from shared.api import make_function
from shared.crud import content_domain
from shared.generated import Education

domain = content_domain(Education, collection="education")
api_education = make_function(domain.router, name="api_education")

__all__ = ["api_education", "domain"]

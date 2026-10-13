"""Profile domain — exports api_profile. A standard content domain, built whole
from its model by shared.crud.content_domain (ADR 0016); deployed alone per ADR 0011."""

from shared.api import make_function
from shared.crud import content_domain
from shared.generated import Profile

domain = content_domain(Profile, collection="profile", singleton_id="main")
api_profile = make_function(domain.router, name="api_profile")

__all__ = ["api_profile", "domain"]

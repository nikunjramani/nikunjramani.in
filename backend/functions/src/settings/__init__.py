"""Settings domain — exports api_settings. A standard content domain, built whole
from its model by shared.crud.content_domain (ADR 0016); deployed alone per ADR 0011."""

from shared.api import make_function
from shared.crud import content_domain
from shared.generated import SiteConfig

domain = content_domain(SiteConfig, collection="site_config", singleton_id="main")
api_settings = make_function(domain.router, name="api_settings")

__all__ = ["api_settings", "domain"]

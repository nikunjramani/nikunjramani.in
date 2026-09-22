from shared.generated import SiteConfig
from shared.repositories.base import BaseRepository


class SiteConfigRepository(BaseRepository[SiteConfig]):
    collection = "site_config"
    model = SiteConfig

"""The `site_config` collection."""

from kernel.crud.repository import BaseRepository
from shared.generated import SiteConfig


class SiteConfigRepository(BaseRepository[SiteConfig]):
    collection = "site_config"
    model = SiteConfig

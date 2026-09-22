from google.cloud.firestore_v1 import Client

from shared.crud import ContentService
from shared.generated import SiteConfig
from src.settings.repository import SiteConfigRepository


class SiteConfigService(ContentService[SiteConfig]):
    def __init__(
        self, db: Client | None = None, *, repo: SiteConfigRepository | None = None
    ) -> None:
        super().__init__(repo if repo is not None else SiteConfigRepository(db))

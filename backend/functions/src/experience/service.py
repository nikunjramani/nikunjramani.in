from google.cloud.firestore_v1 import Client

from shared.crud import ContentService
from shared.generated import Experience
from src.experience.repository import ExperienceRepository


class ExperienceService(ContentService[Experience]):
    def __init__(
        self, db: Client | None = None, *, repo: ExperienceRepository | None = None
    ) -> None:
        super().__init__(repo if repo is not None else ExperienceRepository(db))

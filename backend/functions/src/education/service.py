from google.cloud.firestore_v1 import Client

from shared.crud import ContentService
from shared.generated import Education
from src.education.repository import EducationRepository


class EducationService(ContentService[Education]):
    def __init__(
        self, db: Client | None = None, *, repo: EducationRepository | None = None
    ) -> None:
        super().__init__(repo if repo is not None else EducationRepository(db))

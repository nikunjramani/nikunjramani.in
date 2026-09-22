from google.cloud.firestore_v1 import Client

from shared.crud import ContentService
from shared.generated import Certification
from src.certifications.repository import CertificationRepository


class CertificationService(ContentService[Certification]):
    def __init__(
        self, db: Client | None = None, *, repo: CertificationRepository | None = None
    ) -> None:
        super().__init__(repo if repo is not None else CertificationRepository(db))

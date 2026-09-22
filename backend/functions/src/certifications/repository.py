from shared.generated import Certification
from shared.repositories.base import BaseRepository


class CertificationRepository(BaseRepository[Certification]):
    collection = "certifications"
    model = Certification

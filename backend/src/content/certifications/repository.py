"""The `certifications` collection."""

from kernel.crud.repository import BaseRepository
from shared.generated import Certification


class CertificationRepository(BaseRepository[Certification]):
    collection = "certifications"
    model = Certification

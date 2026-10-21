"""The `education` collection."""

from kernel.crud.repository import BaseRepository
from shared.generated import Education


class EducationRepository(BaseRepository[Education]):
    collection = "education"
    model = Education

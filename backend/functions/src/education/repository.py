from shared.generated import Education
from shared.repositories.base import BaseRepository


class EducationRepository(BaseRepository[Education]):
    collection = "education"
    model = Education

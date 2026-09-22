from shared.generated import Experience
from shared.repositories.base import BaseRepository


class ExperienceRepository(BaseRepository[Experience]):
    collection = "experience"
    model = Experience

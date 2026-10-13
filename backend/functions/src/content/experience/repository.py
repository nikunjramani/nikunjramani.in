"""The `experience` collection."""

from kernel.crud.repository import BaseRepository
from shared.generated import Experience


class ExperienceRepository(BaseRepository[Experience]):
    collection = "experience"
    model = Experience

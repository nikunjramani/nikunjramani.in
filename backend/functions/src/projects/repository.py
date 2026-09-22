from shared.generated import Project
from shared.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    collection = "projects"
    model = Project

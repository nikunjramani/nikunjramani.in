"""The `projects` collection."""

from kernel.crud.repository import BaseRepository
from shared.generated import Project


class ProjectRepository(BaseRepository[Project]):
    collection = "projects"
    model = Project

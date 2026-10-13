"""Portfolio projects — the slug is the document id and the URL.

The generic content rules come from CrudService; duplicate (fresh slug, publish state
reset) is the one rule specific to projects."""

from __future__ import annotations

from kernel.crud.service import CrudService
from kernel.records import Record
from shared.generated import Project
from src.content.projects.repository import ProjectRepository


class ProjectService(CrudService[Project]):
    def __init__(self, repo: ProjectRepository | None = None) -> None:
        super().__init__(repo if repo is not None else ProjectRepository())

    def duplicate(self, doc_id: str, claims: dict[str, object]) -> Record[Project]:
        original = self.repo.require(doc_id)

        new_slug = self._unique_copy_slug(original.data.slug)
        data = original.data.model_dump(mode="json", exclude_none=True)
        data["slug"] = new_slug
        data["title"] = f"{original.data.title} (copy)"
        data["visibility"] = "draft"
        data["featured"] = False
        data["pinned"] = False
        data.pop("audit", None)

        copy = Project.model_validate(data)
        return self.create(copy, claims, doc_id=new_slug)

    def _unique_copy_slug(self, base_slug: str) -> str:
        candidate = f"{base_slug}-copy"
        n = 2
        while self.repo.exists(candidate):
            candidate = f"{base_slug}-copy-{n}"
            n += 1
        return candidate

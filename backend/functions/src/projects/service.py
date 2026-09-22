"""Projects use the generic ContentService for everything except duplication, which is
specific enough (needs a fresh slug, resets publish state) to not belong in shared/."""

from __future__ import annotations

from google.cloud.firestore_v1 import Client

from shared.core.errors import NotFoundError
from shared.core.timestamps import now_iso
from shared.crud import ContentService
from shared.generated import Project
from shared.repositories.base import Record
from src.projects.repository import ProjectRepository


class ProjectService(ContentService[Project]):
    def __init__(self, db: Client | None = None, *, repo: ProjectRepository | None = None) -> None:
        super().__init__(repo if repo is not None else ProjectRepository(db))

    def duplicate(self, doc_id: str, claims: dict[str, object]) -> Record[Project]:
        original = self.repo.get(doc_id)
        if original is None:
            raise NotFoundError(f"Project '{doc_id}' not found.")

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


__all__ = ["ProjectService", "now_iso"]

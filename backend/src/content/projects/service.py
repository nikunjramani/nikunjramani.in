"""Portfolio projects — the slug is the document id and the URL.

The generic content rules come from CrudService. Specific to projects: duplicate (fresh
slug, publish state reset), `unlisted` pages reachable by URL, a confidential client
stripped from public reads, and slugs that would collide with a route reserved."""

from __future__ import annotations

from kernel.crud.service import CrudService
from kernel.errors import ValidationError
from kernel.records import Record
from kernel.security import Actor
from shared.generated import Project
from src.content.projects.repository import ProjectRepository

# Fixed path segments under /api/v1/content/projects/ — a project slugged like one would be
# unreachable at GET /{doc_id}.
RESERVED_SLUGS = frozenset({"public", "reorder"})


class ProjectService(CrudService[Project]):
    # `unlisted` is shareable by link but never listed (list_public filters to `public`).
    reachable_by_url = frozenset({"public", "unlisted"})

    def __init__(self, repo: ProjectRepository | None = None) -> None:
        super().__init__(repo if repo is not None else ProjectRepository())

    def create(
        self, payload: Project, actor: Actor, *, doc_id: str | None = None
    ) -> Record[Project]:
        if payload.slug in RESERVED_SLUGS:
            raise ValidationError(f"slug '{payload.slug}' is reserved.")
        return super().create(payload, actor, doc_id=doc_id)

    def to_public(self, record: Record[Project]) -> Record[Project]:
        """`client.confidential` means nothing identifying the client leaves the API — not
        the name, not the logo. Stripped here, the one place every public read passes."""
        record = super().to_public(record)
        client = record.data.client
        if client is None or not client.confidential:
            return record
        stripped = client.model_copy(update={"name": None, "logoUrl": None})
        return Record(id=record.id, data=record.data.model_copy(update={"client": stripped}))

    def duplicate(self, doc_id: str, actor: Actor) -> Record[Project]:
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
        return self.create(copy, actor, doc_id=new_slug)

    def _unique_copy_slug(self, base_slug: str) -> str:
        candidate = f"{base_slug}-copy"
        n = 2
        while self.repo.exists(candidate):
            candidate = f"{base_slug}-copy-{n}"
            n += 1
        return candidate

"""The site owner's profile — one document, profile/main.

The generic rules (audit stamps, publish transitions, merge-patch) come from CrudService;
this service pins every operation to the single document."""

from __future__ import annotations

from typing import Any

from kernel.crud.service import CrudService
from kernel.records import Record
from kernel.security import Actor
from shared.generated import Profile
from src.content.profile.repository import ProfileRepository

DOC_ID = "main"


class ProfileService(CrudService[Profile]):
    def __init__(self, repo: ProfileRepository | None = None) -> None:
        super().__init__(repo if repo is not None else ProfileRepository())

    def read(self) -> Record[Profile]:
        """404 until it's saved once — nothing creates the document automatically."""
        return self.get(DOC_ID)

    def read_public(self) -> Record[Profile]:
        return self.get_public(DOC_ID)

    def replace(self, payload: Profile, actor: Actor) -> Record[Profile]:
        return self.upsert(DOC_ID, payload, actor)

    def update(self, patch: dict[str, Any], actor: Actor) -> Record[Profile]:
        return self.patch(DOC_ID, patch, actor)

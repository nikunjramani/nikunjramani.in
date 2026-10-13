"""Roles held, with real start/end dates (ADR 0008).

Everything here is the generic content rule set (audit stamps, publish transitions,
merge-patch, reorder) from CrudService — `experience` has no rules of its own yet.
Add them here."""

from __future__ import annotations

from kernel.crud.service import CrudService
from shared.generated import Experience
from src.content.experience.repository import ExperienceRepository


class ExperienceService(CrudService[Experience]):
    def __init__(self, repo: ExperienceRepository | None = None) -> None:
        super().__init__(repo if repo is not None else ExperienceRepository())

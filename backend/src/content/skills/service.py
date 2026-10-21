"""Skills, grouped by category on the public site.

Everything here is the generic content rule set (audit stamps, publish transitions,
merge-patch, reorder) from CrudService — `skills` has no rules of its own yet.
Add them here."""

from __future__ import annotations

from kernel.crud.service import CrudService
from shared.generated import Skill
from src.content.skills.repository import SkillRepository


class SkillService(CrudService[Skill]):
    def __init__(self, repo: SkillRepository | None = None) -> None:
        super().__init__(repo if repo is not None else SkillRepository())

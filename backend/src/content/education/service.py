"""Degrees and schooling.

Everything here is the generic content rule set (audit stamps, publish transitions,
merge-patch, reorder) from CrudService — `education` has no rules of its own yet.
Add them here."""

from __future__ import annotations

from kernel.crud.service import CrudService
from shared.generated import Education
from src.content.education.repository import EducationRepository


class EducationService(CrudService[Education]):
    def __init__(self, repo: EducationRepository | None = None) -> None:
        super().__init__(repo if repo is not None else EducationRepository())

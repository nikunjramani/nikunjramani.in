"""Certifications and their credentials.

Everything here is the generic content rule set (audit stamps, publish transitions,
merge-patch, reorder) from CrudService — `certifications` has no rules of its own yet.
Add them here."""

from __future__ import annotations

from kernel.crud.service import CrudService
from shared.generated import Certification
from src.content.certifications.repository import CertificationRepository


class CertificationService(CrudService[Certification]):
    def __init__(self, repo: CertificationRepository | None = None) -> None:
        super().__init__(repo if repo is not None else CertificationRepository())

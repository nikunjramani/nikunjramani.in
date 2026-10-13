"""Site-wide flags — one document, site_config/main.

The generic rules (audit stamps, publish transitions, merge-patch) come from CrudService;
this service pins every operation to the single document."""

from __future__ import annotations

from typing import Any

from kernel.crud.service import CrudService
from kernel.records import Record
from shared.generated import SiteConfig
from src.content.settings.repository import SiteConfigRepository

DOC_ID = "main"


class SiteConfigService(CrudService[SiteConfig]):
    def __init__(self, repo: SiteConfigRepository | None = None) -> None:
        super().__init__(repo if repo is not None else SiteConfigRepository())

    def read(self) -> Record[SiteConfig]:
        """404 until it's saved once — nothing creates the document automatically."""
        return self.get(DOC_ID)

    def replace(self, payload: SiteConfig, claims: dict[str, object]) -> Record[SiteConfig]:
        return self.upsert(DOC_ID, payload, claims)

    def update(self, patch: dict[str, Any], claims: dict[str, object]) -> Record[SiteConfig]:
        return self.patch(DOC_ID, patch, claims)

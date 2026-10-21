"""content/settings — HTTP routes: admin read/write plus the public site's read.
One fixed document, so no id in any path and no
list/create/delete/reorder. HTTP only: authorise, delegate, serialise."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from kernel.security import AdminClaims
from shared.generated import SiteConfig
from src.content.settings.schemas import SiteConfigOut
from src.content.settings.service import SiteConfigService

router = APIRouter()


def get_settings_service() -> SiteConfigService:
    return SiteConfigService()


Service = Annotated[SiteConfigService, Depends(get_settings_service)]


@router.get("/public", response_model=SiteConfigOut, response_model_exclude_none=True)
def read_public_settings(service: Service) -> SiteConfigOut:
    """The public site's read — no auth. 404 unless the document is `public` (ADR 0022)."""
    return SiteConfigOut.of(service.read_public())


@router.get("/", response_model=SiteConfigOut)
def read_settings(claims: AdminClaims, service: Service) -> SiteConfigOut:
    return SiteConfigOut.of(service.read())


@router.put("/", response_model=SiteConfigOut)
def replace_settings(payload: SiteConfig, claims: AdminClaims, service: Service) -> SiteConfigOut:
    return SiteConfigOut.of(service.replace(payload, claims))


@router.patch("/", response_model=SiteConfigOut)
def update_settings(patch: dict[str, Any], claims: AdminClaims, service: Service) -> SiteConfigOut:
    """RFC 7386 merge patch: `null` removes a field."""
    return SiteConfigOut.of(service.update(patch, claims))

"""content/profile — HTTP routes: admin read/write plus the public site's read.
One fixed document, so no id in any path and no
list/create/delete/reorder. HTTP only: authorise, delegate, serialise."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from kernel.security import AdminClaims
from shared.generated import Profile
from src.content.profile.schemas import ProfileOut
from src.content.profile.service import ProfileService

router = APIRouter()


def get_profile_service() -> ProfileService:
    return ProfileService()


Service = Annotated[ProfileService, Depends(get_profile_service)]


@router.get("/public", response_model=ProfileOut, response_model_exclude_none=True)
def read_public_profile(service: Service) -> ProfileOut:
    """The public site's read — no auth. 404 unless the document is `public` (ADR 0022)."""
    return ProfileOut.of(service.read_public())


@router.get("/", response_model=ProfileOut)
def read_profile(claims: AdminClaims, service: Service) -> ProfileOut:
    return ProfileOut.of(service.read())


@router.put("/", response_model=ProfileOut)
def replace_profile(payload: Profile, claims: AdminClaims, service: Service) -> ProfileOut:
    return ProfileOut.of(service.replace(payload, claims))


@router.patch("/", response_model=ProfileOut)
def update_profile(patch: dict[str, Any], claims: AdminClaims, service: Service) -> ProfileOut:
    """RFC 7386 merge patch: `null` removes a field."""
    return ProfileOut.of(service.update(patch, claims))

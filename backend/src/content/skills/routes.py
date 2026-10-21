"""content/skills — HTTP routes for the `skills` collection: admin
CRUD plus the public site's read.

HTTP only: authorise, delegate to the service, serialise. /public and /reorder are
declared before /{doc_id} so neither is captured as an id."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response

from kernel.security import Admin
from shared.generated import Skill
from src.content.skills.schemas import ReorderIn, SkillOut
from src.content.skills.service import SkillService

router = APIRouter()


def get_skills_service() -> SkillService:
    return SkillService()


Service = Annotated[SkillService, Depends(get_skills_service)]


@router.get("/public", response_model=list[SkillOut], response_model_exclude_none=True)
def list_public_skills(service: Service) -> list[SkillOut]:
    """The public site's read — no auth: `public` documents only, in order (ADR 0022)."""
    return [SkillOut.of(r) for r in service.list_public()]


@router.get("/", response_model=list[SkillOut])
def list_skills(
    admin: Admin,
    service: Service,
    visibility: Annotated[str | None, Query()] = None,
) -> list[SkillOut]:
    return [SkillOut.of(r) for r in service.list_records(visibility)]


@router.post("/", response_model=SkillOut, status_code=201)
def create_skills(payload: Skill, admin: Admin, service: Service) -> SkillOut:
    return SkillOut.of(service.create(payload, admin, doc_id=None))


@router.post("/reorder", status_code=204)
def reorder_skills(body: ReorderIn, admin: Admin, service: Service) -> Response:
    service.reorder(body.ids, admin)
    return Response(status_code=204)


@router.get("/{doc_id}", response_model=SkillOut)
def read_skills(doc_id: str, admin: Admin, service: Service) -> SkillOut:
    return SkillOut.of(service.get(doc_id))


@router.patch("/{doc_id}", response_model=SkillOut)
def update_skills(doc_id: str, patch: dict[str, Any], admin: Admin, service: Service) -> SkillOut:
    """RFC 7386 merge patch: `null` removes a field."""
    return SkillOut.of(service.patch(doc_id, patch, admin))


@router.delete("/{doc_id}", status_code=204)
def delete_skills(doc_id: str, admin: Admin, service: Service) -> Response:
    service.delete(doc_id, admin)
    return Response(status_code=204)

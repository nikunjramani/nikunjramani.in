"""content/projects — HTTP routes for the `projects` collection: admin
CRUD plus the public site's read.

HTTP only: authorise, delegate to the service, serialise. /public and /reorder are
declared before /{doc_id} so neither is captured as an id."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response

from kernel.security import AdminClaims
from shared.generated import Project
from src.content.projects.schemas import ProjectOut, ReorderIn
from src.content.projects.service import ProjectService

router = APIRouter()


def get_projects_service() -> ProjectService:
    return ProjectService()


Service = Annotated[ProjectService, Depends(get_projects_service)]


@router.get("/public", response_model=list[ProjectOut], response_model_exclude_none=True)
def list_public_projects(service: Service) -> list[ProjectOut]:
    """The public site's read — no auth: `public` documents only, in order (ADR 0022)."""
    return [ProjectOut.of(r) for r in service.list_public()]


@router.get("/public/{doc_id}", response_model=ProjectOut, response_model_exclude_none=True)
def read_public_projects(doc_id: str, service: Service) -> ProjectOut:
    """A project page — no auth. `unlisted` is served here but never listed; anything else
    is a 404, same as an id that doesn't exist."""
    return ProjectOut.of(service.get_public(doc_id))


@router.get("/", response_model=list[ProjectOut])
def list_projects(
    claims: AdminClaims,
    service: Service,
    visibility: Annotated[str | None, Query()] = None,
) -> list[ProjectOut]:
    return [ProjectOut.of(r) for r in service.list_records(visibility)]


@router.post("/", response_model=ProjectOut, status_code=201)
def create_projects(payload: Project, claims: AdminClaims, service: Service) -> ProjectOut:
    # The slug is the document id: it is the public URL, so it can't change later.
    return ProjectOut.of(service.create(payload, claims, doc_id=payload.slug))


@router.post("/reorder", status_code=204)
def reorder_projects(body: ReorderIn, claims: AdminClaims, service: Service) -> Response:
    service.reorder(body.ids, claims)
    return Response(status_code=204)


@router.get("/{doc_id}", response_model=ProjectOut)
def read_projects(doc_id: str, claims: AdminClaims, service: Service) -> ProjectOut:
    return ProjectOut.of(service.get(doc_id))


@router.patch("/{doc_id}", response_model=ProjectOut)
def update_projects(
    doc_id: str, patch: dict[str, Any], claims: AdminClaims, service: Service
) -> ProjectOut:
    """RFC 7386 merge patch: `null` removes a field."""
    return ProjectOut.of(service.patch(doc_id, patch, claims))


@router.delete("/{doc_id}", status_code=204)
def delete_projects(doc_id: str, claims: AdminClaims, service: Service) -> Response:
    service.delete(doc_id, claims)
    return Response(status_code=204)


@router.post("/{doc_id}/duplicate", response_model=ProjectOut, status_code=201)
def duplicate_project(doc_id: str, claims: AdminClaims, service: Service) -> ProjectOut:
    return ProjectOut.of(service.duplicate(doc_id, claims))

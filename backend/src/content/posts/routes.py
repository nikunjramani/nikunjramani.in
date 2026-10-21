"""content/posts — admin HTTP routes for the `posts` collection.

HTTP only: authorise, delegate to the service, serialise. /reorder is declared before
/{doc_id} so it isn't captured as an id."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, Response

from kernel.security import Admin
from shared.generated import Post
from src.content.posts.schemas import PostOut, ReorderIn
from src.content.posts.service import PostService

router = APIRouter()


def get_posts_service() -> PostService:
    return PostService()


Service = Annotated[PostService, Depends(get_posts_service)]


@router.get("/", response_model=list[PostOut])
def list_posts(
    admin: Admin,
    service: Service,
    visibility: Annotated[str | None, Query()] = None,
) -> list[PostOut]:
    return [PostOut.of(r) for r in service.list_records(visibility)]


@router.post("/", response_model=PostOut, status_code=201)
def create_posts(payload: Post, admin: Admin, service: Service) -> PostOut:
    # The slug is the document id: it is the public URL, so it can't change later.
    return PostOut.of(service.create(payload, admin, doc_id=payload.slug))


@router.post("/reorder", status_code=204)
def reorder_posts(body: ReorderIn, admin: Admin, service: Service) -> Response:
    service.reorder(body.ids, admin)
    return Response(status_code=204)


@router.get("/{doc_id}", response_model=PostOut)
def read_posts(doc_id: str, admin: Admin, service: Service) -> PostOut:
    return PostOut.of(service.get(doc_id))


@router.patch("/{doc_id}", response_model=PostOut)
def update_posts(doc_id: str, patch: dict[str, Any], admin: Admin, service: Service) -> PostOut:
    """RFC 7386 merge patch: `null` removes a field."""
    return PostOut.of(service.patch(doc_id, patch, admin))


@router.delete("/{doc_id}", status_code=204)
def delete_posts(doc_id: str, admin: Admin, service: Service) -> Response:
    service.delete(doc_id, admin)
    return Response(status_code=204)

"""inbox/messages — admin HTTP routes. /export.csv is declared before /{doc_id} so it isn't
captured as an id."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from kernel.security import AdminClaims
from src.inbox.messages.schemas import MessageOut
from src.inbox.messages.service import MessageService

router = APIRouter()


def get_messages_service() -> MessageService:
    return MessageService()


Service = Annotated[MessageService, Depends(get_messages_service)]


@router.get("/", response_model=list[MessageOut])
def list_messages(
    claims: AdminClaims, service: Service, unread_only: Annotated[bool, Query()] = False
) -> list[MessageOut]:
    return [MessageOut.of(r) for r in service.list_all(unread_only=unread_only)]


@router.get("/export.csv")
def export_messages(claims: AdminClaims, service: Service) -> Response:
    return Response(
        content=service.export_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=messages.csv"},
    )


@router.get("/{doc_id}", response_model=MessageOut)
def get_message(doc_id: str, claims: AdminClaims, service: Service) -> MessageOut:
    return MessageOut.of(service.get(doc_id))


@router.patch("/{doc_id}/read", response_model=MessageOut)
def mark_message_read(doc_id: str, claims: AdminClaims, service: Service) -> MessageOut:
    return MessageOut.of(service.mark_read(doc_id, claims))


@router.patch("/{doc_id}/replied", response_model=MessageOut)
def mark_message_replied(doc_id: str, claims: AdminClaims, service: Service) -> MessageOut:
    return MessageOut.of(service.mark_replied(doc_id, claims))


@router.delete("/{doc_id}", status_code=204)
def delete_message(doc_id: str, claims: AdminClaims, service: Service) -> Response:
    service.delete(doc_id, claims)
    return Response(status_code=204)

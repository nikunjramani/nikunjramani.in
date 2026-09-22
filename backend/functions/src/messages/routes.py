from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel

from shared.core.security import AdminClaims
from shared.generated import ContactMessage
from src.messages.service import MessageService

router = APIRouter()


def get_messages_service() -> MessageService:
    return MessageService()


class RecordOut(BaseModel):
    id: str
    data: ContactMessage


@router.get("/", response_model=list[RecordOut])
def list_messages(
    claims: AdminClaims,
    service: Annotated[MessageService, Depends(get_messages_service)],
    unread_only: Annotated[bool, Query()] = False,
) -> list[dict[str, object]]:
    return [{"id": r.id, "data": r.data} for r in service.list_all(unread_only=unread_only)]


@router.get("/export.csv")
def export_messages(
    claims: AdminClaims, service: Annotated[MessageService, Depends(get_messages_service)]
) -> Response:
    return Response(
        content=service.export_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=messages.csv"},
    )


@router.get("/{doc_id}", response_model=RecordOut)
def get_message(
    doc_id: str,
    claims: AdminClaims,
    service: Annotated[MessageService, Depends(get_messages_service)],
) -> dict[str, object]:
    record = service.get(doc_id)
    return {"id": record.id, "data": record.data}


@router.patch("/{doc_id}/read", response_model=RecordOut)
def mark_message_read(
    doc_id: str,
    claims: AdminClaims,
    service: Annotated[MessageService, Depends(get_messages_service)],
) -> dict[str, object]:
    record = service.mark_read(doc_id)
    return {"id": record.id, "data": record.data}


@router.patch("/{doc_id}/replied", response_model=RecordOut)
def mark_message_replied(
    doc_id: str,
    claims: AdminClaims,
    service: Annotated[MessageService, Depends(get_messages_service)],
) -> dict[str, object]:
    record = service.mark_replied(doc_id)
    return {"id": record.id, "data": record.data}


@router.delete("/{doc_id}", status_code=204)
def delete_message(
    doc_id: str,
    claims: AdminClaims,
    service: Annotated[MessageService, Depends(get_messages_service)],
) -> Response:
    service.delete(doc_id)
    return Response(status_code=204)

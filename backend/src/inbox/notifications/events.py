"""inbox/notifications — HTTP entry point: Eventarc delivers Firestore `document.created`
events for contact_messages/{id} here (POST /internal/events/contact-created).

HTTP only: verify the caller, read the event, delegate. Delivery is at-least-once: a failed send
raises and Eventarc retries, and a repeat is harmless (the send carries an idempotency key)."""

from __future__ import annotations

from fastapi import APIRouter, Request, Response
from starlette.concurrency import run_in_threadpool

from kernel.events import InternalCaller, firestore_document
from src.inbox.notifications.service import notify_owner

router = APIRouter(dependencies=[InternalCaller])


@router.post("/contact-created", status_code=204)
async def contact_created(request: Request) -> Response:
    doc_id, data = await firestore_document(request)
    await run_in_threadpool(notify_owner, doc_id, data)
    return Response(status_code=204)

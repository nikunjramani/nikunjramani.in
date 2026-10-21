"""media/processing — HTTP entry point: Eventarc delivers the media bucket's
`object.finalized` events here (POST /internal/events/media-uploaded).

HTTP only: verify the caller, read the event, delegate. The service already ignores anything
that isn't a new raw upload, and events are at-least-once, so a 204 means "handled or nothing
to do"; a raised error is a 5xx, which Eventarc retries."""

from __future__ import annotations

from fastapi import APIRouter, Request, Response
from starlette.concurrency import run_in_threadpool

from kernel.events import InternalCaller, storage_object
from src.media.processing.service import ProcessingService

router = APIRouter(dependencies=[InternalCaller])


@router.post("/media-uploaded", status_code=204)
async def media_uploaded(request: Request) -> Response:
    obj = await storage_object(request)
    # Image work is CPU-bound — off the event loop, so it can't stall other requests.
    await run_in_threadpool(
        ProcessingService().handle_upload, obj.name, uploaded_by=obj.metadata.get("uploadedBy")
    )
    return Response(status_code=204)

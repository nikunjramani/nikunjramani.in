"""media/processing — entry point: deploys on_media_uploaded (Storage trigger)."""

from firebase_functions import storage_fn
from firebase_functions.core import CloudEvent

from src.media.processing.service import ProcessingService
from src.media.processing.settings import get_media_settings


# The bucket must be a real string at decoration time — this runs on import.
@storage_fn.on_object_finalized(
    bucket=get_media_settings().storage_bucket, region="asia-south1", memory=1024, max_instances=2
)
def on_media_uploaded(event: CloudEvent[storage_fn.StorageObjectData]) -> None:
    ProcessingService().handle_upload(
        event.data.name, uploaded_by=(event.data.metadata or {}).get("uploadedBy")
    )

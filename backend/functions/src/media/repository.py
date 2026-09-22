from shared.generated import MediaAsset
from shared.repositories.base import BaseRepository


class MediaRepository(BaseRepository[MediaAsset]):
    collection = "media_assets"
    model = MediaAsset

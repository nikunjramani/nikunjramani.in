from google.cloud.firestore_v1 import Client

from shared.crud import ContentService
from shared.generated import Profile
from src.profile.repository import ProfileRepository


class ProfileService(ContentService[Profile]):
    def __init__(self, db: Client | None = None, *, repo: ProfileRepository | None = None) -> None:
        super().__init__(repo if repo is not None else ProfileRepository(db))

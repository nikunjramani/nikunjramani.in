from shared.generated import Profile
from shared.repositories.base import BaseRepository


class ProfileRepository(BaseRepository[Profile]):
    collection = "profile"
    model = Profile

"""The `profile` collection."""

from kernel.crud.repository import BaseRepository
from shared.generated import Profile


class ProfileRepository(BaseRepository[Profile]):
    collection = "profile"
    model = Profile

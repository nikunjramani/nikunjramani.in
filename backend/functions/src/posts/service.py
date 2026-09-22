from google.cloud.firestore_v1 import Client

from shared.crud import ContentService
from shared.generated import Post
from src.posts.repository import PostRepository


class PostService(ContentService[Post]):
    def __init__(self, db: Client | None = None, *, repo: PostRepository | None = None) -> None:
        super().__init__(repo if repo is not None else PostRepository(db))

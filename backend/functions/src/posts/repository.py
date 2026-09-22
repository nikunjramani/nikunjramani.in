from shared.generated import Post
from shared.repositories.base import BaseRepository


class PostRepository(BaseRepository[Post]):
    collection = "posts"
    model = Post

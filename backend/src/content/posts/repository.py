"""The `posts` collection."""

from kernel.crud.repository import BaseRepository
from shared.generated import Post


class PostRepository(BaseRepository[Post]):
    collection = "posts"
    model = Post

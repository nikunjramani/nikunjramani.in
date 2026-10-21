"""Blog posts — the slug is the document id and the URL.

Everything here is the generic content rule set (audit stamps, publish transitions,
merge-patch, reorder) from CrudService — `posts` has no rules of its own yet.
Add them here."""

from __future__ import annotations

from kernel.crud.service import CrudService
from shared.generated import Post
from src.content.posts.repository import PostRepository


class PostService(CrudService[Post]):
    def __init__(self, repo: PostRepository | None = None) -> None:
        super().__init__(repo if repo is not None else PostRepository())

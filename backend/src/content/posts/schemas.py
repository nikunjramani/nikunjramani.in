"""Wire shapes for content/posts.

Requests are the Post model itself, validated by FastAPI against the generated
schema; responses carry the document id beside it."""

from kernel.crud.schemas import RecordOut, ReorderIn
from shared.generated import Post


class PostOut(RecordOut[Post]):
    """A posts document as the admin API returns it."""


__all__ = ["PostOut", "ReorderIn"]

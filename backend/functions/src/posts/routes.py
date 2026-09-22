from fastapi import APIRouter

from shared.crud import make_crud_router
from shared.generated import Post
from src.posts.service import PostService

router = APIRouter()


def get_posts_service() -> PostService:
    return PostService()


router.include_router(make_crud_router(model=Post, get_service=get_posts_service, slugged=True))

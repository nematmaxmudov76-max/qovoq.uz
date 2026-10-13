from fastapi import APIRouter

from app.api.v1 import auth, comments, posts, tags, users

router = APIRouter()

router.include_router(auth.router)
router.include_router(posts.router)
router.include_router(comments.router)
router.include_router(tags.router)
router.include_router(users.router)

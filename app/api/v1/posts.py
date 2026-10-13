from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_session
from app.models.user import User
from app.schemas.post import PostCreate, PostDetail, PostListResponse, PostUpdate
from app.services.post_service import PostService

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("/", response_model=PostListResponse)
async def list_posts(
    tag: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
) -> PostListResponse:
    service = PostService(session)
    return await service.list_posts(tag_slug=tag, search=search, page=page, per_page=per_page)


@router.post("/", response_model=PostDetail, status_code=201)
async def create_post(
    data: PostCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PostDetail:
    service = PostService(session)
    return await service.create_post(data, current_user)


@router.get("/{slug}", response_model=PostDetail)
async def get_post(
    slug: str,
    session: AsyncSession = Depends(get_session),
) -> PostDetail:
    service = PostService(session)
    return await service.get_post_by_slug(slug, increment_views=True)


@router.patch("/{slug}", response_model=PostDetail)
async def update_post(
    slug: str,
    data: PostUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PostDetail:
    service = PostService(session)
    return await service.update_post(slug, data, current_user)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    slug: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    service = PostService(session)
    await service.delete_post(slug, current_user)


@router.post("/{post_id}/like")
async def toggle_like(
    post_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    service = PostService(session)
    return await service.toggle_like(post_id, current_user)

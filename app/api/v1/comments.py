from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_session
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentOut, CommentUpdate
from app.services.comment_service import CommentService

router = APIRouter(tags=["comments"])


@router.get("/posts/{post_id}/comments", response_model=List[CommentOut])
async def list_comments(
    post_id: int,
    session: AsyncSession = Depends(get_session),
) -> List[CommentOut]:
    service = CommentService(session)
    return await service.get_post_comments(post_id)


@router.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=201)
async def create_comment(
    post_id: int,
    data: CommentCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CommentOut:
    service = CommentService(session)
    return await service.create_comment(post_id, data, current_user)


@router.patch("/comments/{comment_id}", response_model=CommentOut)
async def update_comment(
    comment_id: int,
    data: CommentUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> CommentOut:
    service = CommentService(session)
    return await service.update_comment(comment_id, data, current_user)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    service = CommentService(session)
    await service.delete_comment(comment_id, current_user)

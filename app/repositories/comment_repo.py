from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.comment import Comment


class CommentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, comment_id: int) -> Optional[Comment]:
        stmt = (
            select(Comment)
            .where(Comment.id == comment_id)
            .options(
                joinedload(Comment.author),
                selectinload(Comment.replies).options(joinedload(Comment.author)),
            )
        )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_post(self, post_id: int) -> List[Comment]:
        """Returns all comments for the post ordered by created_at."""
        stmt = (
            select(Comment)
            .where(Comment.post_id == post_id)
            .options(joinedload(Comment.author))
            .order_by(Comment.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.unique().scalars().all())

    async def create(self, comment: Comment) -> Comment:
        self._session.add(comment)
        await self._session.commit()
        await self._session.refresh(comment)
        # Reload with author loaded
        res = await self.get_by_id(comment.id)
        return res if res is not None else comment

    async def save(self, comment: Comment) -> Comment:
        await self._session.commit()
        await self._session.refresh(comment)
        res = await self.get_by_id(comment.id)
        return res if res is not None else comment

    async def delete(self, comment: Comment) -> None:
        await self._session.delete(comment)
        await self._session.commit()

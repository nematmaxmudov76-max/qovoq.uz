from typing import List

from fastapi import HTTPException, status
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comment import Comment
from app.models.user import User
from app.repositories.comment_repo import CommentRepository
from app.schemas.comment import (
    CommentAuthorOut,
    CommentCreate,
    CommentOut,
    CommentUpdate,
)


class CommentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CommentRepository(session)

    def _to_out(self, comment: Comment) -> CommentOut:
        state = inspect(comment)
        replies: List[CommentOut] = []
        if "replies" not in state.unloaded:
            replies = [self._to_out(r) for r in comment.replies]

        return CommentOut(
            id=comment.id,
            text=comment.text,
            post_id=comment.post_id,
            parent_id=comment.parent_id,
            author=CommentAuthorOut(
                id=comment.author.id, username=comment.author.username
            ),
            replies=replies,
            created_at=comment.created_at,
        )

    async def get_post_comments(self, post_id: int) -> List[CommentOut]:
        comments = await self._repo.get_by_post(post_id)
        comment_map: dict[int, CommentOut] = {}
        for c in comments:
            comment_map[c.id] = CommentOut(
                id=c.id,
                text=c.text,
                post_id=c.post_id,
                parent_id=c.parent_id,
                author=CommentAuthorOut(id=c.author.id, username=c.author.username),
                replies=[],
                created_at=c.created_at,
            )

        roots: List[CommentOut] = []
        for c in comments:
            node = comment_map[c.id]
            if c.parent_id is not None and c.parent_id in comment_map:
                comment_map[c.parent_id].replies.append(node)
            else:
                roots.append(node)

        return roots

    async def create_comment(
        self, post_id: int, data: CommentCreate, user: User
    ) -> CommentOut:
        if data.parent_id is not None:
            parent = await self._repo.get_by_id(data.parent_id)
            if parent is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent comment not found",
                )
            if parent.post_id != post_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent comment belongs to a different post",
                )

        comment = Comment(
            text=data.text,
            user_id=user.id,
            post_id=post_id,
            parent_id=data.parent_id,
        )
        comment = await self._repo.create(comment)
        return self._to_out(comment)

    async def update_comment(
        self, comment_id: int, data: CommentUpdate, user: User
    ) -> CommentOut:
        comment = await self._repo.get_by_id(comment_id)
        if comment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
            )
        if comment.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not the owner"
            )
        comment.text = data.text
        comment = await self._repo.save(comment)
        return self._to_out(comment)

    async def delete_comment(self, comment_id: int, user: User) -> None:
        comment = await self._repo.get_by_id(comment_id)
        if comment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found"
            )
        if comment.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Not the owner"
            )
        await self._repo.delete(comment)

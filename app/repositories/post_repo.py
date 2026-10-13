import math
from typing import List, Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models.comment import Comment
from app.models.post import Post
from app.models.tag import Tag


class PostRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_slug(self, slug: str) -> Optional[Post]:
        stmt = (
            select(Post)
            .where(Post.slug == slug)
            .options(
                joinedload(Post.author),
                selectinload(Post.tags),
                selectinload(Post.likes),
                selectinload(Post.comments).options(
                    joinedload(Comment.author),
                    selectinload(Comment.replies).options(joinedload(Comment.author)),
                ),
            )
        )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_by_id(self, post_id: int) -> Optional[Post]:
        stmt = (
            select(Post)
            .where(Post.id == post_id)
            .options(
                joinedload(Post.author),
                selectinload(Post.tags),
                selectinload(Post.likes),
                selectinload(Post.comments).options(
                    joinedload(Comment.author),
                    selectinload(Comment.replies).options(joinedload(Comment.author)),
                ),
            )
        )
        result = await self._session.execute(stmt)
        return result.unique().scalar_one_or_none()

    async def get_list(
        self,
        tag_slug: Optional[str] = None,
        author_id: Optional[int] = None,
        search: Optional[str] = None,
        page: int = 1,
        per_page: int = 10,
    ) -> tuple[List[Post], int]:
        filter_stmt = select(Post.id)

        if tag_slug:
            filter_stmt = filter_stmt.join(Post.tags).where(Tag.slug == tag_slug)

        if author_id is not None:
            filter_stmt = filter_stmt.where(Post.user_id == author_id)

        if search:
            pattern = f"%{search}%"
            filter_stmt = filter_stmt.where(
                Post.title.ilike(pattern) | Post.content.ilike(pattern)
            )

        count_stmt = select(func.count()).select_from(filter_stmt.subquery())
        total_result = await self._session.execute(count_stmt)
        total: int = total_result.scalar_one()

        stmt = (
            select(Post)
            .options(
                joinedload(Post.author),
                selectinload(Post.tags),
                selectinload(Post.likes),
            )
        )

        if tag_slug:
            stmt = stmt.join(Post.tags).where(Tag.slug == tag_slug)

        if author_id is not None:
            stmt = stmt.where(Post.user_id == author_id)

        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                Post.title.ilike(pattern) | Post.content.ilike(pattern)
            )

        offset = (page - 1) * per_page
        stmt = stmt.order_by(Post.created_at.desc()).offset(offset).limit(per_page)
        result = await self._session.execute(stmt)
        posts = result.unique().scalars().all()

        return list(posts), total

    async def create(self, post: Post) -> Post:
        self._session.add(post)
        await self._session.commit()
        await self._session.refresh(post)
        return post

    async def save(self, post: Post) -> Post:
        await self._session.commit()
        await self._session.refresh(post)
        return post

    async def delete(self, post: Post) -> None:
        await self._session.delete(post)
        await self._session.commit()

    async def slug_exists(self, slug: str) -> bool:
        result = await self._session.execute(
            select(func.count()).where(Post.slug == slug)
        )
        return result.scalar_one() > 0

    async def increment_views(self, post: Post) -> None:
        await self._session.execute(
            update(Post).where(Post.id == post.id).values(views=Post.views + 1)
        )
        await self._session.commit()
        post.views += 1

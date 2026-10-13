import math
from typing import List, Optional

from fastapi import HTTPException, status
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.like import Like
from app.models.post import Post
from app.models.tag import Tag
from app.models.user import User
from app.repositories.post_repo import PostRepository
from app.schemas.post import PostCreate, PostDetail, PostList, PostListResponse, PostUpdate


class PostService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = PostRepository(session)

    async def _build_slug(self, title: str) -> str:
        base = slugify(title)
        if not await self._repo.slug_exists(base):
            return base
        # Append incrementing suffix until unique
        counter = 1
        while True:
            candidate = f"{base}-{counter}"
            if not await self._repo.slug_exists(candidate):
                return candidate
            counter += 1

    async def _fetch_tags(self, tag_ids: List[int]) -> List[Tag]:
        if not tag_ids:
            return []
        result = await self._session.execute(
            select(Tag).where(Tag.id.in_(tag_ids))
        )
        return list(result.scalars().all())

    def _to_post_detail(self, post: Post) -> PostDetail:
        return PostDetail(
            id=post.id,
            title=post.title,
            slug=post.slug,
            content=post.content,
            excerpt=post.excerpt,
            is_published=post.is_published,
            views=post.views,
            author={"id": post.author.id, "username": post.author.username},
            tags=[{"id": t.id, "name": t.name, "slug": t.slug} for t in post.tags],
            like_count=len(post.likes),
            comment_count=len(post.comments),
            created_at=post.created_at,
            updated_at=post.updated_at,
        )

    def _to_post_list(self, post: Post) -> PostList:
        return PostList(
            id=post.id,
            title=post.title,
            slug=post.slug,
            excerpt=post.excerpt,
            is_published=post.is_published,
            views=post.views,
            author={"id": post.author.id, "username": post.author.username},
            tags=[{"id": t.id, "name": t.name, "slug": t.slug} for t in post.tags],
            like_count=len(post.likes),
            created_at=post.created_at,
        )

    async def create_post(self, data: PostCreate, user: User) -> PostDetail:
        slug = await self._build_slug(data.title)
        tags = await self._fetch_tags(data.tag_ids)

        post = Post(
            title=data.title,
            slug=slug,
            content=data.content,
            excerpt=data.excerpt,
            is_published=data.is_published,
            user_id=user.id,
            tags=tags,
        )
        post = await self._repo.create(post)
        # Reload with all relationships
        post = await self._repo.get_by_id(post.id)  # type: ignore[assignment]
        return self._to_post_detail(post)

    async def get_post_by_slug(self, slug: str, increment_views: bool = False) -> PostDetail:
        post = await self._repo.get_by_slug(slug)
        if post is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        if increment_views:
            await self._repo.increment_views(post)
        return self._to_post_detail(post)

    async def list_posts(
        self,
        tag_slug: Optional[str],
        search: Optional[str],
        page: int,
        per_page: int,
    ) -> PostListResponse:
        posts, total = await self._repo.get_list(
            tag_slug=tag_slug, search=search, page=page, per_page=per_page
        )
        pages = math.ceil(total / per_page) if per_page else 1
        return PostListResponse(
            items=[self._to_post_list(p) for p in posts],
            total=total,
            page=page,
            pages=pages,
        )

    async def update_post(self, slug: str, data: PostUpdate, user: User) -> PostDetail:
        post = await self._repo.get_by_slug(slug)
        if post is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        if post.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the owner")

        if data.title is not None and data.title != post.title:
            post.title = data.title
            post.slug = await self._build_slug(data.title)
        if data.content is not None:
            post.content = data.content
        if data.excerpt is not None:
            post.excerpt = data.excerpt
        if data.is_published is not None:
            post.is_published = data.is_published
        if data.tag_ids is not None:
            post.tags = await self._fetch_tags(data.tag_ids)

        await self._repo.save(post)
        post = await self._repo.get_by_id(post.id)  # type: ignore[assignment]
        return self._to_post_detail(post)

    async def delete_post(self, slug: str, user: User) -> None:
        post = await self._repo.get_by_slug(slug)
        if post is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
        if post.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the owner")
        await self._repo.delete(post)

    async def toggle_like(self, post_id: int, user: User) -> dict:
        result = await self._session.execute(
            select(Like).where(Like.user_id == user.id, Like.post_id == post_id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            await self._session.delete(existing)
            await self._session.commit()
            return {"liked": False}
        else:
            # Verify post exists
            post_result = await self._session.execute(
                select(Post).where(Post.id == post_id)
            )
            if post_result.scalar_one_or_none() is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
            like = Like(user_id=user.id, post_id=post_id)
            self._session.add(like)
            await self._session.commit()
            return {"liked": True}

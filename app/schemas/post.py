from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.tag import TagOut


class AuthorOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    username: str


class PostCreate(BaseModel):
    title: str
    content: str
    excerpt: Optional[str] = None
    is_published: bool = False
    tag_ids: List[int] = []


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    is_published: Optional[bool] = None
    tag_ids: Optional[List[int]] = None


class PostList(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    title: str
    slug: str
    excerpt: Optional[str]
    is_published: bool
    views: int
    author: AuthorOut
    tags: List[TagOut]
    like_count: int = 0
    created_at: datetime


class PostDetail(PostList):
    content: str
    comment_count: int = 0
    updated_at: datetime


class PostListResponse(BaseModel):
    items: List[PostList]
    total: int
    page: int
    pages: int

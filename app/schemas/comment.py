from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class CommentAuthorOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    username: str


class CommentCreate(BaseModel):
    text: str
    parent_id: Optional[int] = None


class CommentUpdate(BaseModel):
    text: str


class CommentOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    text: str
    post_id: int
    parent_id: Optional[int]
    author: CommentAuthorOut
    replies: List["CommentOut"] = []
    created_at: datetime


CommentOut.model_rebuild()

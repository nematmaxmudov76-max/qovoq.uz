from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None


class UserOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime


class UserProfile(UserOut):
    post_count: int = 0


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

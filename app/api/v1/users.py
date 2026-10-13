from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_session
from app.core.security import hash_password
from app.models.post import Post
from app.models.user import User
from app.schemas.user import UserOut, UserProfile, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)


@router.get("/{username}", response_model=UserProfile)
async def get_user_profile(
    username: str,
    session: AsyncSession = Depends(get_session),
) -> UserProfile:
    result = await session.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    count_result = await session.execute(
        select(func.count()).where(Post.user_id == user.id)
    )
    post_count = count_result.scalar_one()

    profile = UserProfile.model_validate(user)
    profile.post_count = post_count
    return profile


@router.patch("/me", response_model=UserOut)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    if data.username is not None:
        exists = await session.execute(
            select(User).where(User.username == data.username, User.id != current_user.id)
        )
        if exists.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
            )
        current_user.username = data.username

    if data.email is not None:
        exists = await session.execute(
            select(User).where(User.email == data.email, User.id != current_user.id)
        )
        if exists.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
            )
        current_user.email = data.email

    if data.password is not None:
        current_user.hashed_pw = hash_password(data.password)

    await session.commit()
    await session.refresh(current_user)
    return UserOut.model_validate(current_user)

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_session
from app.schemas.user import TokenOut, UserOut, UserRegister
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(
    data: UserRegister,
    session: AsyncSession = Depends(get_session),
) -> UserOut:
    service = AuthService(session)
    user = await service.register(data)
    return UserOut.model_validate(user)


@router.post("/login", response_model=TokenOut)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
) -> TokenOut:
    service = AuthService(session)
    return await service.login(form.username, form.password)


@router.post("/refresh")
async def refresh_token(
    payload: dict,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Body: {"refresh_token": "<token>"}"""
    service = AuthService(session)
    return await service.refresh(payload.get("refresh_token", ""))

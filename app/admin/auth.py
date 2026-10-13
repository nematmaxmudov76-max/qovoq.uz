from typing import Optional

from sqlalchemy import select
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminUser, AuthProvider
from starlette_admin.exceptions import LoginFailed

from app.core.config import settings
from app.core.security import verify_password
from app.db.session import AsyncSessionLocal
from app.models.user import User


class AdminAuthProvider(AuthProvider):
    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
    ) -> Optional[Response]:
        # 1. Primary check: configured environment admin credentials
        if (
            username == settings.ADMIN_USERNAME
            and password == settings.ADMIN_PASSWORD
        ):
            request.session["admin_user"] = {
                "username": username,
                "email": "admin@blog.local",
            }
            return None

        # 2. Database user check: authenticate active registered users
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(
                (User.username == username) | (User.email == username)
            )
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if (
                user is not None
                and user.is_active
                and verify_password(password, user.hashed_pw)
            ):
                request.session["admin_user"] = {
                    "username": user.username,
                    "email": user.email,
                }
                return None

        raise LoginFailed("Invalid username or password")

    async def authenticate(self, request: Request) -> Optional[AdminUser]:
        admin_data = request.session.get("admin_user")
        if admin_data:
            return AdminUser(username=admin_data["username"])
        return None

    async def logout(self, request: Request) -> Optional[Response]:
        request.session.clear()
        return None

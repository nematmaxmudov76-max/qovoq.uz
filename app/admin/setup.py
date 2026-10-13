from fastapi import FastAPI
from starlette_admin.contrib.sqla import Admin

from app.admin.auth import AdminAuthProvider
from app.admin.views import (
    CommentView,
    LikeView,
    PostView,
    TagView,
    UserView,
)
from app.core.config import settings
from app.db.session import engine
from app.models.comment import Comment
from app.models.like import Like
from app.models.post import Post
from app.models.tag import Tag
from app.models.user import User


def create_admin() -> Admin:
    admin = Admin(
        engine,
        title=f"{settings.APP_TITLE} Panel",
        base_url="/admin",
        route_name="admin",
        auth_provider=AdminAuthProvider(),
        secret_key=settings.SECRET_KEY,
    )

    admin.add_view(UserView(User))
    admin.add_view(PostView(Post))
    admin.add_view(CommentView(Comment))
    admin.add_view(TagView(Tag))
    admin.add_view(LikeView(Like))

    return admin


def setup_admin(app: FastAPI) -> Admin:
    admin = create_admin()
    admin.mount_to(app)
    return admin

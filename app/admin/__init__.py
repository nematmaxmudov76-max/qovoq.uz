from app.admin.auth import AdminAuthProvider
from app.admin.setup import create_admin, setup_admin
from app.admin.views import (
    CommentView,
    LikeView,
    PostView,
    TagView,
    UserView,
)

__all__ = [
    "setup_admin",
    "create_admin",
    "AdminAuthProvider",
    "UserView",
    "PostView",
    "CommentView",
    "TagView",
    "LikeView",
]

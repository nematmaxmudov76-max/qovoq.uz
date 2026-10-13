from typing import Any, Dict

from slugify import slugify
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView

from app.core.security import hash_password
from app.models.comment import Comment
from app.models.like import Like
from app.models.post import Post
from app.models.tag import Tag
from app.models.user import User


class UserView(ModelView):
    identity = "user"
    name = "User"
    label = "Users"
    icon = "fa fa-users"
    exclude_fields_from_list = ["hashed_pw"]
    exclude_fields_from_detail = ["hashed_pw"]
    searchable_fields = ["username", "email"]
    sortable_fields = ["id", "username", "email", "is_active", "created_at"]

    async def before_create(
        self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        if "hashed_pw" in data and data["hashed_pw"]:
            obj.hashed_pw = hash_password(str(data["hashed_pw"]))

    async def before_edit(
        self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        if (
            "hashed_pw" in data
            and data["hashed_pw"]
            and not str(data["hashed_pw"]).startswith("$2b$")
        ):
            obj.hashed_pw = hash_password(str(data["hashed_pw"]))


class PostView(ModelView):
    identity = "post"
    name = "Post"
    label = "Posts"
    icon = "fa fa-newspaper"
    exclude_fields_from_list = ["content"]
    searchable_fields = ["title", "slug", "content"]
    sortable_fields = ["id", "title", "views", "is_published", "created_at"]

    async def before_create(
        self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        if not getattr(obj, "slug", None) and getattr(obj, "title", None):
            obj.slug = slugify(obj.title)


class CommentView(ModelView):
    identity = "comment"
    name = "Comment"
    label = "Comments"
    icon = "fa fa-comments"
    searchable_fields = ["text"]
    sortable_fields = ["id", "created_at"]


class TagView(ModelView):
    identity = "tag"
    name = "Tag"
    label = "Tags"
    icon = "fa fa-tags"
    searchable_fields = ["name", "slug"]
    sortable_fields = ["id", "name", "slug"]

    async def before_create(
        self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        if not getattr(obj, "slug", None) and getattr(obj, "name", None):
            obj.slug = slugify(obj.name)


class LikeView(ModelView):
    identity = "like"
    name = "Like"
    label = "Likes"
    icon = "fa fa-thumbs-up"
    sortable_fields = ["id", "user_id", "post_id"]

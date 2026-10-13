from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from slugify import slugify
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_session
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tag import TagCreate, TagOut

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("/", response_model=List[TagOut])
async def list_tags(session: AsyncSession = Depends(get_session)) -> List[TagOut]:
    result = await session.execute(select(Tag).order_by(Tag.name))
    tags = result.scalars().all()
    return [TagOut.model_validate(t) for t in tags]


@router.post("/", response_model=TagOut, status_code=201)
async def create_tag(
    data: TagCreate,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> TagOut:
    slug = slugify(data.name)

    existing = await session.execute(select(Tag).where(Tag.slug == slug))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Tag already exists"
        )

    tag = Tag(name=data.name, slug=slug)
    session.add(tag)
    await session.commit()
    await session.refresh(tag)
    return TagOut.model_validate(tag)

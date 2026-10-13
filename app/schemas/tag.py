from pydantic import BaseModel


class TagCreate(BaseModel):
    name: str


class TagOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    slug: str

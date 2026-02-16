from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class CategoryRead(CategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

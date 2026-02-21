from datetime import datetime
import base64
import binascii

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ItemBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    item_code: str = Field(min_length=3, max_length=40)
    category_id: int
    stock: int = Field(ge=0)

    @field_validator("item_code")
    @classmethod
    def validate_item_code(cls, value: str) -> str:
        cleaned = value.strip().upper()
        if not cleaned:
            raise ValueError("item_code cannot be empty")
        return cleaned


class ItemCreate(ItemBase):
    photos_base64: list[str] | None = None

    @field_validator("photos_base64")
    @classmethod
    def validate_photos_base64(cls, value: list[str] | None) -> list[str] | None:
        if not value:
            return None
        valid_photos = []
        for photo in value:
            if not photo:
                continue
            base64_data = photo.split("base64,", maxsplit=1)[-1]
            try:
                raw = base64.b64decode(base64_data, validate=True)
            except (ValueError, binascii.Error) as exc:
                raise ValueError("One of the photos is not valid base64") from exc

            if len(raw) > 0:
                valid_photos.append(photo)
        
        return valid_photos if valid_photos else None


class ItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    item_code: str | None = Field(default=None, min_length=3, max_length=40)
    category_id: int | None = None
    stock: int | None = Field(default=None, ge=0)
    photos_base64: list[str] | None = None

    @field_validator("item_code")
    @classmethod
    def validate_update_item_code(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip().upper()
        if not cleaned:
            raise ValueError("item_code cannot be empty")
        return cleaned

    @field_validator("photos_base64")
    @classmethod
    def validate_update_photos_base64(cls, value: list[str] | None) -> list[str] | None:
        if not value:
            return None
        valid_photos = []
        for photo in value:
            if not photo:
                continue
            base64_data = photo.split("base64,", maxsplit=1)[-1]
            try:
                raw = base64.b64decode(base64_data, validate=True)
            except (ValueError, binascii.Error) as exc:
                raise ValueError("One of the photos is not valid base64") from exc

            if len(raw) > 0:
                valid_photos.append(photo)
        
        return valid_photos if valid_photos else None


class ItemPhotoRead(BaseModel):
    id: int
    photo_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ItemRead(ItemBase):
    id: int
    created_at: datetime
    has_photo: bool
    photo_url: str | None = None
    additional_photos: list[ItemPhotoRead] = []

    model_config = ConfigDict(from_attributes=True)

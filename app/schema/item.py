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
        if not cleaned.isalnum():
            raise ValueError("item_code must be alphanumeric")
        if not any(ch.isalpha() for ch in cleaned) or not any(ch.isdigit() for ch in cleaned):
            raise ValueError("item_code must contain letters and numbers")
        return cleaned


class ItemCreate(ItemBase):
    photo_base64: str
    photo_content_type: str = Field(default="image/jpeg", min_length=3, max_length=100)

    @field_validator("photo_base64")
    @classmethod
    def validate_photo_base64(cls, value: str) -> str:
        base64_data = value.split("base64,", maxsplit=1)[-1]
        try:
            raw = base64.b64decode(base64_data, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ValueError("photo_base64 is not valid base64") from exc

        if len(raw) == 0:
            raise ValueError("photo_base64 cannot be empty")
        return value


class ItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    item_code: str | None = Field(default=None, min_length=3, max_length=40)
    category_id: int | None = None
    stock: int | None = Field(default=None, ge=0)
    photo_base64: str | None = None
    photo_content_type: str | None = Field(default=None, min_length=3, max_length=100)

    @field_validator("item_code")
    @classmethod
    def validate_update_item_code(cls, value: str | None) -> str | None:
        if value is None:
            return value
        cleaned = value.strip().upper()
        if not cleaned.isalnum():
            raise ValueError("item_code must be alphanumeric")
        if not any(ch.isalpha() for ch in cleaned) or not any(ch.isdigit() for ch in cleaned):
            raise ValueError("item_code must contain letters and numbers")
        return cleaned

    @field_validator("photo_base64")
    @classmethod
    def validate_update_photo_base64(cls, value: str | None) -> str | None:
        if value is None:
            return value
        base64_data = value.split("base64,", maxsplit=1)[-1]
        try:
            raw = base64.b64decode(base64_data, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ValueError("photo_base64 is not valid base64") from exc

        if len(raw) == 0:
            raise ValueError("photo_base64 cannot be empty")
        return value


class ItemRead(ItemBase):
    id: int
    created_at: datetime
    has_photo: bool
    photo_content_type: str

    model_config = ConfigDict(from_attributes=True)

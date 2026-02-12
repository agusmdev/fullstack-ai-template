"""Item schemas - request and response models."""

import uuid

from pydantic import BaseModel, Field

from app.core.optional_model import partial_model
from app.database.mixins import OrmBaseModel


class ItemBase(BaseModel):
    """Base item schema with common fields."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=5000)


class ItemCreate(ItemBase):
    """Schema for creating a new item."""

    pass


@partial_model
class ItemUpdate(ItemBase):
    """Schema for updating an item (all fields optional)."""

    pass


class ItemResponse(ItemBase, OrmBaseModel):
    """Schema for item response (includes timestamps and id)."""

    id: uuid.UUID

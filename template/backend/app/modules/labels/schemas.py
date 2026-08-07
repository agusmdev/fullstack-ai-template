"""Label schemas — request and response models."""

import uuid

from pydantic import BaseModel, Field

from app.core.optional_model import partial_model
from app.database.mixins import OrmBaseModel


class LabelBase(BaseModel):
    """Common editable label fields (no team_id — it is a scoping key)."""

    name: str = Field(..., min_length=1, max_length=255)
    color: str | None = Field(default=None, max_length=32)


class LabelCreate(LabelBase):
    """Schema for creating a new label (team_id required for scoping)."""

    team_id: uuid.UUID


@partial_model
class LabelUpdate(LabelBase):
    """Schema for updating a label (all fields optional)."""

    pass


class LabelResponse(LabelBase, OrmBaseModel):
    """Label response including id and team_id."""

    id: uuid.UUID
    team_id: uuid.UUID

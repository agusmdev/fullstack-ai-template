"""View schemas — request and response models."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.core.optional_model import partial_model
from app.database.mixins import OrmBaseModel


class ViewBase(BaseModel):
    """Common editable view fields (no team_id — it is a scoping key)."""

    name: str = Field(..., min_length=1, max_length=255)
    filters: dict[str, Any] = Field(default_factory=dict)
    group_by: str | None = None
    order_by: str | None = None
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        """Reject whitespace-only names (treat as empty) — VAL-VIEWS-002."""
        if not v or not v.strip():
            raise ValueError("Name must not be empty or whitespace-only")
        return v


class ViewCreate(ViewBase):
    """Schema for creating a saved view (team_id required for scoping)."""

    team_id: uuid.UUID


@partial_model
class ViewUpdate(ViewBase):
    """Schema for updating a saved view (all fields optional)."""

    pass


class ViewResponse(ViewBase, OrmBaseModel):
    """View response including id, owner_id, team_id, and timestamps."""

    id: uuid.UUID
    owner_id: uuid.UUID | None
    team_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

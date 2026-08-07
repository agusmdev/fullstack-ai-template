"""Cycle schemas — request and response models.

Enforces ``ends_at > starts_at`` at the schema layer so an invalid date range
returns a 422 validation error (VAL-CYCLES-002). The validator is tolerant of
``None`` values so it also works on the ``@partial_model`` update schema where
fields are individually optional.
"""

import uuid
from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator

from app.core.optional_model import partial_model
from app.database.mixins import OrmBaseModel


class CycleBase(BaseModel):
    """Common editable cycle fields (no team_id — it is a scoping key)."""

    name: str = Field(..., min_length=1, max_length=255)
    starts_at: date
    ends_at: date
    completed_at: date | None = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        """Reject whitespace-only names (treat as empty)."""
        if not v or not v.strip():
            raise ValueError("Name must not be empty or whitespace-only")
        return v

    @model_validator(mode="after")
    def end_must_be_after_start(self) -> Self:
        """Enforce ``ends_at > starts_at`` when both are present (VAL-CYCLES-002).

        Tolerates ``None`` so this validator also works on the partial update
        schema where either date may be omitted individually. The service-layer
        update resolves a single provided date against the stored entity.
        """
        if self.starts_at is not None and self.ends_at is not None:
            if self.ends_at <= self.starts_at:
                raise ValueError("ends_at must be after starts_at")
        return self


class CycleCreate(CycleBase):
    """Schema for creating a new cycle (team_id required for scoping)."""

    team_id: uuid.UUID


@partial_model
class CycleUpdate(CycleBase):
    """Schema for updating a cycle (all fields optional)."""

    pass


class CycleResponse(CycleBase, OrmBaseModel):
    """Cycle response including id and team_id."""

    id: uuid.UUID
    team_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

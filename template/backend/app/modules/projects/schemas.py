"""Project schemas — request and response models."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.core.optional_model import partial_model
from app.database.mixins import OrmBaseModel
from app.modules.projects.models import ProjectStatus


class ProjectBase(BaseModel):
    """Common editable project fields (no team_id — it is a scoping key)."""

    name: str = Field(..., min_length=1, max_length=255)
    status: ProjectStatus = ProjectStatus.planned
    lead_id: uuid.UUID | None = None
    target_date: date | None = None
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, v: str) -> str:
        """Reject whitespace-only names (treat as empty)."""
        if not v or not v.strip():
            raise ValueError("Name must not be empty or whitespace-only")
        return v


class ProjectCreate(ProjectBase):
    """Schema for creating a new project (team_id required for scoping)."""

    team_id: uuid.UUID


@partial_model
class ProjectUpdate(ProjectBase):
    """Schema for updating a project (all fields optional)."""

    pass


class ProjectResponse(ProjectBase, OrmBaseModel):
    """Project response including id and team_id."""

    id: uuid.UUID
    team_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

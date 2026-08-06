"""Issue schemas — request and response models."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.optional_model import partial_model
from app.database.mixins import OrmBaseModel


class IssueLabelBrief(BaseModel):
    """Lightweight label info embedded in issue responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    color: str | None = None


class IssueBase(BaseModel):
    """Common editable issue fields (no team_id / identifier — scoping/server-set)."""

    title: str = Field(..., min_length=1, max_length=512)
    description: str | None = None
    status_id: uuid.UUID | None = None
    priority: int = Field(default=4, ge=0, le=4)
    assignee_id: uuid.UUID | None = None
    sort_order: float = 0.0
    estimate: float | None = None
    due_date: datetime | None = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: str) -> str:
        """Reject whitespace-only titles (treat as empty)."""
        if not v or not v.strip():
            raise ValueError("Title must not be empty or whitespace-only")
        return v


class IssueCreate(IssueBase):
    """Schema for creating a new issue.

    ``team_id`` is required for scoping. ``status_id`` defaults to the team's
    first workflow state (backlog) when omitted. ``label_ids`` optionally
    attaches labels on create.
    """

    team_id: uuid.UUID
    label_ids: list[uuid.UUID] | None = None
    parent_id: uuid.UUID | None = None


@partial_model
class IssueUpdate(IssueBase):
    """Schema for updating an issue (all fields optional)."""

    parent_id: uuid.UUID | None = None


class IssueResponse(IssueBase, OrmBaseModel):
    """Issue response with server-generated fields and embedded labels."""

    id: uuid.UUID
    team_id: uuid.UUID
    identifier: str
    creator_id: uuid.UUID
    project_id: uuid.UUID | None = None
    cycle_id: uuid.UUID | None = None
    parent_id: uuid.UUID | None = None
    labels: list[IssueLabelBrief] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

"""Comment schemas — request and response models."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.database.mixins import OrmBaseModel


class AuthorBrief(BaseModel):
    """Lightweight author info embedded in a comment response.

    Carries just enough (id, display_name, email) for the SPA to render the
    comment author without a second fetch (VAL-COMMENTS-004).
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_name: str
    email: str


class CommentCreate(BaseModel):
    """Schema for creating a comment.

    The author is derived from the authenticated user (``user_id``); the body
    must be non-empty (validated in the service layer — whitespace-only is
    rejected with 422, VAL-COMMENTS-002).
    """

    issue_id: uuid.UUID = Field(..., description="The issue this comment belongs to")
    body: str = Field(..., description="The comment text (non-empty)")


class CommentUpdate(BaseModel):
    """Schema for editing a comment body (partial).

    Only the author (or a team admin) may edit (VAL-COMMENTS-005, VAL-COMMENTS-008).
    """

    body: str = Field(..., description="The updated comment text (non-empty)")


class CommentResponse(OrmBaseModel):
    """Comment response with the nested author brief."""

    id: uuid.UUID
    issue_id: uuid.UUID
    author_id: uuid.UUID
    body: str
    author: AuthorBrief
    created_at: datetime
    updated_at: datetime

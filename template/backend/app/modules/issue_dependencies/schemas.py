"""IssueDependency schemas — request and response models."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.database.mixins import OrmBaseModel


class DependencyIssueBrief(BaseModel):
    """Lightweight issue info embedded in a dependency response.

    Carries just enough (identifier, title, priority, status) for the SPA to
    render a dependency row on either side of the relationship without a second
    fetch (VAL-DEPS-002).
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    identifier: str
    title: str
    priority: int
    status_id: uuid.UUID


class IssueDependencyCreate(BaseModel):
    """Schema for creating a dependency.

    Only the ``blocks`` relation is supported; ``relation`` is therefore not a
    client-set field (the model defaults it to ``"blocks"``).
    """

    blocker_id: uuid.UUID = Field(
        ..., description="The issue that blocks (A in 'A blocks B')"
    )
    blocked_id: uuid.UUID = Field(
        ..., description="The issue that is blocked (B in 'A blocks B')"
    )


class IssueDependencyResponse(OrmBaseModel):
    """Dependency response with nested blocker/blocked issue briefs."""

    id: uuid.UUID
    blocker_id: uuid.UUID
    blocked_id: uuid.UUID
    relation: str
    blocker: DependencyIssueBrief
    blocked: DependencyIssueBrief
    created_at: datetime
    updated_at: datetime

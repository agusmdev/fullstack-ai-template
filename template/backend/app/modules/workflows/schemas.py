"""WorkflowState schemas — request and response models."""

import uuid

from pydantic import BaseModel, Field

from app.core.optional_model import partial_model
from app.database.mixins import OrmBaseModel
from app.modules.workflows.models import WorkflowStateType


class WorkflowStateBase(BaseModel):
    """Common editable workflow-state fields (no team_id — it is a scoping key)."""

    name: str = Field(..., min_length=1, max_length=255)
    type: WorkflowStateType
    position: float = 0.0
    color: str | None = Field(default=None, max_length=32)


class WorkflowStateCreate(WorkflowStateBase):
    """Schema for creating a new workflow state (team_id required for scoping)."""

    team_id: uuid.UUID


@partial_model
class WorkflowStateUpdate(WorkflowStateBase):
    """Schema for updating a workflow state (all fields optional)."""

    pass


class WorkflowStateResponse(WorkflowStateBase, OrmBaseModel):
    """WorkflowState response including id and team_id."""

    id: uuid.UUID
    team_id: uuid.UUID

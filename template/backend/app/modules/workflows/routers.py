"""WorkflowStates router — CRUD endpoints for WorkflowState entities."""

import uuid
from typing import cast

from fastapi import APIRouter, Body, Depends, Query, status
from fastapi_pagination import Page, Params

from app.core.logging import log_action, log_entity
from app.modules.workflows.dependencies import get_workflow_state_service
from app.modules.workflows.filters import WorkflowStateFilter
from app.modules.workflows.schemas import (
    WorkflowStateCreate,
    WorkflowStateResponse,
    WorkflowStateUpdate,
)
from app.modules.workflows.service import WorkflowStateService
from app.user.auth import require_current_user_id

workflow_states_router = APIRouter(
    prefix="/workflow-states",
    tags=["workflow-states"],
    dependencies=[Depends(require_current_user_id)],
)


@workflow_states_router.get(
    "",
    response_description="List workflow states",
    status_code=status.HTTP_200_OK,
)
async def list_workflow_states(
    pagination: Params = Depends(),
    workflow_filter: WorkflowStateFilter = Depends(),
    team_id: uuid.UUID | None = Query(
        default=None, description="Restrict to a single team"
    ),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: WorkflowStateService = Depends(get_workflow_state_service),
) -> Page[WorkflowStateResponse]:
    """List workflow states for the authenticated user's teams."""
    log_action("list")
    result = await service.get_all_paginated(
        pagination_params=pagination,
        entity_filter=workflow_filter,
        user_id=user_id,
        team_id=team_id,
    )
    return cast(
        "Page[WorkflowStateResponse]",
        Page[WorkflowStateResponse].model_validate(
            {
                "items": [
                    WorkflowStateResponse.model_validate(s) for s in result.items
                ],
                "total": result.total,
                "page": result.page,
                "size": result.size,
                "pages": result.pages,
            }
        ),
    )


@workflow_states_router.get(
    "/{state_id}",
    response_description="Get workflow state by ID",
    status_code=status.HTTP_200_OK,
)
async def get_workflow_state(
    state_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: WorkflowStateService = Depends(get_workflow_state_service),
) -> WorkflowStateResponse:
    """Get a workflow state by ID, enforcing team membership."""
    log_action("get")
    result = await service.get_by_id(state_id, user_id=user_id)
    return WorkflowStateResponse.model_validate(result)


@workflow_states_router.post(
    "",
    response_description="Create a new workflow state",
    status_code=status.HTTP_201_CREATED,
)
async def create_workflow_state(
    state: WorkflowStateCreate = Body(...),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: WorkflowStateService = Depends(get_workflow_state_service),
) -> WorkflowStateResponse:
    """Create a new workflow state (admin only)."""
    log_action("create")
    result = await service.create(state, user_id=user_id)
    log_entity("workflow_state", result.id)
    return WorkflowStateResponse.model_validate(result)


@workflow_states_router.patch(
    "/{state_id}",
    response_description="Update a workflow state",
    status_code=status.HTTP_200_OK,
)
async def update_workflow_state(
    state_id: uuid.UUID,
    state: WorkflowStateUpdate = Body(...),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: WorkflowStateService = Depends(get_workflow_state_service),
) -> WorkflowStateResponse:
    """Update an existing workflow state (admin only)."""
    log_action("update")
    log_entity("workflow_state", state_id)
    result = await service.update(state_id, state, user_id=user_id)
    return WorkflowStateResponse.model_validate(result)


@workflow_states_router.delete(
    "/{state_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Delete a workflow state",
)
async def delete_workflow_state(
    state_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: WorkflowStateService = Depends(get_workflow_state_service),
) -> None:
    """Delete a workflow state by ID (admin only)."""
    log_action("delete")
    log_entity("workflow_state", state_id)
    await service.delete(state_id, user_id=user_id)

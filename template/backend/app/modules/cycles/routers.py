"""Cycles router — CRUD endpoints for Cycle entities."""

import uuid
from typing import cast

from fastapi import APIRouter, Body, Depends, Query, status
from fastapi_pagination import Page, Params

from app.core.logging import log_action, log_entity
from app.modules.cycles.dependencies import get_cycle_service
from app.modules.cycles.filters import CycleFilter
from app.modules.cycles.schemas import (
    CycleCreate,
    CycleResponse,
    CycleUpdate,
)
from app.modules.cycles.service import CycleService
from app.user.auth import require_current_user_id

cycles_router = APIRouter(
    prefix="/cycles",
    tags=["cycles"],
    dependencies=[Depends(require_current_user_id)],
)


@cycles_router.get(
    "",
    response_description="List cycles",
    status_code=status.HTTP_200_OK,
)
async def list_cycles(
    pagination: Params = Depends(),
    cycle_filter: CycleFilter = Depends(),
    team_id: uuid.UUID | None = Query(default=None, description="Restrict to a team"),
    order_by: list[str] | None = Query(
        default=None,
        description="Sort fields (prefix '-' for desc, e.g. -created_at, -starts_at)",
    ),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: CycleService = Depends(get_cycle_service),
) -> Page[CycleResponse]:
    """List cycles for the authenticated user's teams."""
    log_action("list")
    # Override the filter's order_by — FastAPI's Depends() doesn't parse
    # list[str] fields from query params, so we extract order_by via Query().
    if order_by is not None:
        cycle_filter.order_by = order_by
    result = await service.get_all_paginated(
        pagination_params=pagination,
        entity_filter=cycle_filter,
        user_id=user_id,
        team_id=team_id,
    )
    return cast(
        "Page[CycleResponse]",
        Page[CycleResponse].model_validate(
            {
                "items": [
                    CycleResponse.model_validate(cycle) for cycle in result.items
                ],
                "total": result.total,
                "page": result.page,
                "size": result.size,
                "pages": result.pages,
            }
        ),
    )


@cycles_router.get(
    "/{cycle_id}",
    response_description="Get cycle by ID",
    status_code=status.HTTP_200_OK,
)
async def get_cycle(
    cycle_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: CycleService = Depends(get_cycle_service),
) -> CycleResponse:
    """Get a cycle by ID, enforcing team membership."""
    log_action("get")
    result = await service.get_by_id(cycle_id, user_id=user_id)
    return CycleResponse.model_validate(result)


@cycles_router.post(
    "",
    response_description="Create a new cycle",
    status_code=status.HTTP_201_CREATED,
)
async def create_cycle(
    cycle: CycleCreate = Body(...),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: CycleService = Depends(get_cycle_service),
) -> CycleResponse:
    """Create a new cycle (member or admin).

    Requires name + starts_at + ends_at; ends_at must be after starts_at
    (VAL-CYCLES-001, VAL-CYCLES-002).
    """
    log_action("create")
    result = await service.create(cycle, user_id=user_id)
    log_entity("cycle", result.id)
    return CycleResponse.model_validate(result)


@cycles_router.patch(
    "/{cycle_id}",
    response_description="Update a cycle",
    status_code=status.HTTP_200_OK,
)
async def update_cycle(
    cycle_id: uuid.UUID,
    cycle: CycleUpdate = Body(...),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: CycleService = Depends(get_cycle_service),
) -> CycleResponse:
    """Update an existing cycle (member or admin)."""
    log_action("update")
    log_entity("cycle", cycle_id)
    result = await service.update(cycle_id, cycle, user_id=user_id)
    return CycleResponse.model_validate(result)


@cycles_router.delete(
    "/{cycle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Delete a cycle",
)
async def delete_cycle(
    cycle_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: CycleService = Depends(get_cycle_service),
) -> None:
    """Delete a cycle by ID (member or admin). Issues are detached (SET NULL)."""
    log_action("delete")
    log_entity("cycle", cycle_id)
    await service.delete(cycle_id, user_id=user_id)

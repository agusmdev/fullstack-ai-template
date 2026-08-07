"""Views router — CRUD endpoints for saved View entities."""

import uuid
from typing import cast

from fastapi import APIRouter, Body, Depends, Query, status
from fastapi_pagination import Page, Params

from app.core.logging import log_action, log_entity
from app.modules.views.dependencies import get_view_service
from app.modules.views.filters import ViewFilter
from app.modules.views.schemas import (
    ViewCreate,
    ViewResponse,
    ViewUpdate,
)
from app.modules.views.service import ViewService
from app.user.auth import require_current_user_id

views_router = APIRouter(
    prefix="/views",
    tags=["views"],
    dependencies=[Depends(require_current_user_id)],
)


@views_router.get(
    "",
    response_description="List saved views",
    status_code=status.HTTP_200_OK,
)
async def list_views(
    pagination: Params = Depends(),
    view_filter: ViewFilter = Depends(),
    team_id: uuid.UUID | None = Query(default=None, description="Restrict to a team"),
    order_by: list[str] | None = Query(
        default=None,
        description="Sort fields (prefix '-' for desc, e.g. -created_at, name)",
    ),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: ViewService = Depends(get_view_service),
) -> Page[ViewResponse]:
    """List saved views for the authenticated user's teams."""
    log_action("list")
    # Override the filter's order_by — FastAPI's Depends() doesn't parse
    # list[str] fields from query params, so we extract order_by via Query().
    if order_by is not None:
        view_filter.order_by = order_by
    result = await service.get_all_paginated(
        pagination_params=pagination,
        entity_filter=view_filter,
        user_id=user_id,
        team_id=team_id,
    )
    return cast(
        "Page[ViewResponse]",
        Page[ViewResponse].model_validate(
            {
                "items": [ViewResponse.model_validate(view) for view in result.items],
                "total": result.total,
                "page": result.page,
                "size": result.size,
                "pages": result.pages,
            }
        ),
    )


@views_router.get(
    "/{view_id}",
    response_description="Get saved view by ID",
    status_code=status.HTTP_200_OK,
)
async def get_view(
    view_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: ViewService = Depends(get_view_service),
) -> ViewResponse:
    """Get a saved view by ID, enforcing team membership."""
    log_action("get")
    result = await service.get_by_id(view_id, user_id=user_id)
    return ViewResponse.model_validate(result)


@views_router.post(
    "",
    response_description="Create a saved view",
    status_code=status.HTTP_201_CREATED,
)
async def create_view(
    view: ViewCreate = Body(...),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: ViewService = Depends(get_view_service),
) -> ViewResponse:
    """Create a saved view (member or admin).

    Requires a non-empty name (VAL-VIEWS-002). Captures filters + group_by +
    order_by from the current view configuration (VAL-VIEWS-001).
    """
    log_action("create")
    result = await service.create(view, user_id=user_id)
    log_entity("view", result.id)
    return ViewResponse.model_validate(result)


@views_router.patch(
    "/{view_id}",
    response_description="Update a saved view",
    status_code=status.HTTP_200_OK,
)
async def update_view(
    view_id: uuid.UUID,
    view: ViewUpdate = Body(...),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: ViewService = Depends(get_view_service),
) -> ViewResponse:
    """Update a saved view (member or admin).

    Only reached on an explicit re-save — dirty local changes never invoke this
    (VAL-VIEWS-006).
    """
    log_action("update")
    log_entity("view", view_id)
    result = await service.update(view_id, view, user_id=user_id)
    return ViewResponse.model_validate(result)


@views_router.delete(
    "/{view_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Delete a saved view",
)
async def delete_view(
    view_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: ViewService = Depends(get_view_service),
) -> None:
    """Delete a saved view by ID (member or admin)."""
    log_action("delete")
    log_entity("view", view_id)
    await service.delete(view_id, user_id=user_id)

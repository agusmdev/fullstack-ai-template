"""IssueDependency router — CRUD endpoints for issue 'blocks' relationships."""

import uuid
from typing import cast

from fastapi import APIRouter, Body, Depends, Query, status
from fastapi_pagination import Page, Params

from app.core.logging import log_action, log_entity
from app.modules.issue_dependencies.dependencies import get_issue_dependency_service
from app.modules.issue_dependencies.filters import IssueDependencyFilter
from app.modules.issue_dependencies.schemas import (
    IssueDependencyCreate,
    IssueDependencyResponse,
)
from app.modules.issue_dependencies.service import IssueDependencyService
from app.user.auth import require_current_user_id

issue_dependencies_router = APIRouter(
    prefix="/issue-dependencies",
    tags=["issue-dependencies"],
    dependencies=[Depends(require_current_user_id)],
)


@issue_dependencies_router.get(
    "",
    response_description="List dependencies",
    status_code=status.HTTP_200_OK,
)
async def list_issue_dependencies(
    pagination: Params = Depends(),
    dep_filter: IssueDependencyFilter = Depends(),
    issue_id: uuid.UUID | None = Query(
        default=None,
        description="Restrict to dependencies involving this issue (either side)",
    ),
    team_id: uuid.UUID | None = Query(
        default=None, description="Restrict to a single team"
    ),
    order_by: list[str] | None = Query(
        default=None,
        description="Sort fields (prefix '-' for desc, e.g. -created_at)",
    ),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: IssueDependencyService = Depends(get_issue_dependency_service),
) -> Page[IssueDependencyResponse]:
    """List dependencies for the authenticated user's teams.

    Supports filtering by ``issue_id`` (dependencies involving that issue — used
    for reciprocal display on the issue drawer, VAL-DEPS-002) and ``team_id``.
    """
    log_action("list")
    # Override the filter's order_by — FastAPI's Depends() doesn't parse
    # list[str] fields from query params, so we extract order_by via Query().
    if order_by is not None:
        dep_filter.order_by = order_by
    result = await service.get_all_paginated(
        pagination_params=pagination,
        entity_filter=dep_filter,
        user_id=user_id,
        issue_id=issue_id,
        team_id=team_id,
    )
    return cast(
        "Page[IssueDependencyResponse]",
        Page[IssueDependencyResponse].model_validate(
            {
                "items": [
                    IssueDependencyResponse.model_validate(dep) for dep in result.items
                ],
                "total": result.total,
                "page": result.page,
                "size": result.size,
                "pages": result.pages,
            }
        ),
    )


@issue_dependencies_router.get(
    "/{dependency_id}",
    response_description="Get dependency by ID",
    status_code=status.HTTP_200_OK,
)
async def get_issue_dependency(
    dependency_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: IssueDependencyService = Depends(get_issue_dependency_service),
) -> IssueDependencyResponse:
    """Get a dependency by ID, enforcing team membership."""
    log_action("get")
    result = await service.get_by_id(dependency_id, user_id=user_id)
    return IssueDependencyResponse.model_validate(result)


@issue_dependencies_router.post(
    "",
    response_description="Create a dependency",
    status_code=status.HTTP_201_CREATED,
)
async def create_issue_dependency(
    dependency: IssueDependencyCreate = Body(...),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: IssueDependencyService = Depends(get_issue_dependency_service),
) -> IssueDependencyResponse:
    """Create a 'blocks' dependency ("A blocks B").

    Both endpoints must exist and belong to the same team; cycle-forming edges
    are rejected with 409 (VAL-DEPS-001, VAL-DEPS-003, VAL-DEPS-005).
    """
    log_action("create")
    result = await service.create(dependency, user_id=user_id)
    log_entity("issue_dependency", result.id)
    return IssueDependencyResponse.model_validate(result)


@issue_dependencies_router.delete(
    "/{dependency_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Delete a dependency",
)
async def delete_issue_dependency(
    dependency_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: IssueDependencyService = Depends(get_issue_dependency_service),
) -> None:
    """Delete a dependency by ID (member or admin). Removes it from both issues."""
    log_action("delete")
    log_entity("issue_dependency", dependency_id)
    await service.delete(dependency_id, user_id=user_id)

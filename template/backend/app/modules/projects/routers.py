"""Projects router — CRUD endpoints for Project entities."""

import uuid
from typing import cast

from fastapi import APIRouter, Body, Depends, Query, status
from fastapi_pagination import Page, Params

from app.core.logging import log_action, log_entity
from app.modules.projects.dependencies import get_project_service
from app.modules.projects.filters import ProjectFilter
from app.modules.projects.schemas import (
    ProjectCreate,
    ProjectResponse,
    ProjectUpdate,
)
from app.modules.projects.service import ProjectService
from app.user.auth import require_current_user_id

projects_router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    dependencies=[Depends(require_current_user_id)],
)


@projects_router.get(
    "",
    response_description="List projects",
    status_code=status.HTTP_200_OK,
)
async def list_projects(
    pagination: Params = Depends(),
    project_filter: ProjectFilter = Depends(),
    team_id: uuid.UUID | None = Query(default=None, description="Restrict to a team"),
    order_by: list[str] | None = Query(
        default=None,
        description="Sort fields (prefix '-' for desc, e.g. -created_at, name)",
    ),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: ProjectService = Depends(get_project_service),
) -> Page[ProjectResponse]:
    """List projects for the authenticated user's teams."""
    log_action("list")
    # Override the filter's order_by — FastAPI's Depends() doesn't parse
    # list[str] fields from query params, so we extract order_by via Query().
    if order_by is not None:
        project_filter.order_by = order_by
    result = await service.get_all_paginated(
        pagination_params=pagination,
        entity_filter=project_filter,
        user_id=user_id,
        team_id=team_id,
    )
    return cast(
        "Page[ProjectResponse]",
        Page[ProjectResponse].model_validate(
            {
                "items": [
                    ProjectResponse.model_validate(project) for project in result.items
                ],
                "total": result.total,
                "page": result.page,
                "size": result.size,
                "pages": result.pages,
            }
        ),
    )


@projects_router.get(
    "/{project_id}",
    response_description="Get project by ID",
    status_code=status.HTTP_200_OK,
)
async def get_project(
    project_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """Get a project by ID, enforcing team membership."""
    log_action("get")
    result = await service.get_by_id(project_id, user_id=user_id)
    return ProjectResponse.model_validate(result)


@projects_router.post(
    "",
    response_description="Create a new project",
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    project: ProjectCreate = Body(...),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """Create a new project (member or admin). Defaults status to ``planned``."""
    log_action("create")
    result = await service.create(project, user_id=user_id)
    log_entity("project", result.id)
    return ProjectResponse.model_validate(result)


@projects_router.patch(
    "/{project_id}",
    response_description="Update a project",
    status_code=status.HTTP_200_OK,
)
async def update_project(
    project_id: uuid.UUID,
    project: ProjectUpdate = Body(...),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """Update an existing project (member or admin)."""
    log_action("update")
    log_entity("project", project_id)
    result = await service.update(project_id, project, user_id=user_id)
    return ProjectResponse.model_validate(result)


@projects_router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Delete a project",
)
async def delete_project(
    project_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: ProjectService = Depends(get_project_service),
) -> None:
    """Delete a project by ID (member or admin). Issues are detached (SET NULL)."""
    log_action("delete")
    log_entity("project", project_id)
    await service.delete(project_id, user_id=user_id)

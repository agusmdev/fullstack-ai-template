"""Issues router — CRUD endpoints + labels sub-resource."""

import uuid
from typing import cast

from fastapi import APIRouter, Body, Depends, Query, status
from fastapi_pagination import Page, Params

from app.core.logging import log_action, log_entity
from app.modules.issues.dependencies import get_issue_service
from app.modules.issues.filters import IssueFilter
from app.modules.issues.schemas import (
    IssueCreate,
    IssueResponse,
    IssueUpdate,
)
from app.modules.issues.service import IssueService
from app.user.auth import require_current_user_id

issues_router = APIRouter(
    prefix="/issues",
    tags=["issues"],
    dependencies=[Depends(require_current_user_id)],
)


@issues_router.get(
    "",
    response_description="List issues",
    status_code=status.HTTP_200_OK,
)
async def list_issues(
    pagination: Params = Depends(),
    issue_filter: IssueFilter = Depends(),
    team_id: uuid.UUID | None = Query(
        default=None, description="Restrict to a single team"
    ),
    label_id: uuid.UUID | None = Query(
        default=None, description="Filter by label membership"
    ),
    unassigned: bool | None = Query(
        default=None, description="Filter to issues with no assignee"
    ),
    parent_id: uuid.UUID | None = Query(
        default=None, description="Fetch the children of a specific parent issue"
    ),
    top_level: bool | None = Query(
        default=None, description="Filter to top-level issues (parent_id IS NULL)"
    ),
    order_by: list[str] | None = Query(
        default=None,
        description="Sort fields (prefix '-' for desc, e.g. -created_at, priority)",
    ),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: IssueService = Depends(get_issue_service),
) -> Page[IssueResponse]:
    """List issues for the authenticated user's teams.

    Supports filter (status/priority/assignee/parent via fastapi_filter), search
    (title ilike), sort (created/updated/priority via ``order_by``), pagination,
    label filtering via ``label_id``, an ``unassigned`` flag for issues with
    no assignee (VAL-ISSUES-021), ``parent_id`` to fetch children of a parent
    (VAL-SUBISSUES-001), and ``top_level`` for top-level issues only.
    """
    log_action("list")
    # Override the filter's order_by — FastAPI's Depends() doesn't parse
    # list[str] fields from query params, so we extract order_by via Query().
    if order_by is not None:
        issue_filter.order_by = order_by
    result = await service.get_all_paginated(
        pagination_params=pagination,
        entity_filter=issue_filter,
        user_id=user_id,
        team_id=team_id,
        label_id=label_id,
        unassigned=unassigned,
        parent_id=parent_id,
        top_level=top_level,
    )
    return cast(
        "Page[IssueResponse]",
        Page[IssueResponse].model_validate(
            {
                "items": [
                    IssueResponse.model_validate(issue) for issue in result.items
                ],
                "total": result.total,
                "page": result.page,
                "size": result.size,
                "pages": result.pages,
            }
        ),
    )


@issues_router.get(
    "/{issue_id}",
    response_description="Get issue by ID",
    status_code=status.HTTP_200_OK,
)
async def get_issue(
    issue_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: IssueService = Depends(get_issue_service),
) -> IssueResponse:
    """Get an issue by ID, enforcing team membership."""
    log_action("get")
    result = await service.get_by_id(issue_id, user_id=user_id)
    return IssueResponse.model_validate(result)


@issues_router.post(
    "",
    response_description="Create a new issue",
    status_code=status.HTTP_201_CREATED,
)
async def create_issue(
    issue: IssueCreate = Body(...),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: IssueService = Depends(get_issue_service),
) -> IssueResponse:
    """Create a new issue. Auto-generates the identifier and defaults status."""
    log_action("create")
    result = await service.create(issue, user_id=user_id)
    log_entity("issue", result.id)
    return IssueResponse.model_validate(result)


@issues_router.patch(
    "/{issue_id}",
    response_description="Update an issue",
    status_code=status.HTTP_200_OK,
)
async def update_issue(
    issue_id: uuid.UUID,
    issue: IssueUpdate = Body(...),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: IssueService = Depends(get_issue_service),
) -> IssueResponse:
    """Update an existing issue (member or admin)."""
    log_action("update")
    log_entity("issue", issue_id)
    result = await service.update(issue_id, issue, user_id=user_id)
    return IssueResponse.model_validate(result)


@issues_router.delete(
    "/{issue_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Delete an issue",
)
async def delete_issue(
    issue_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: IssueService = Depends(get_issue_service),
) -> None:
    """Delete an issue by ID (member or admin)."""
    log_action("delete")
    log_entity("issue", issue_id)
    await service.delete(issue_id, user_id=user_id)


# --- Labels sub-resource ------------------------------------------------


@issues_router.post(
    "/{issue_id}/labels/{label_id}",
    response_description="Add a label to an issue",
    status_code=status.HTTP_200_OK,
)
async def add_label(
    issue_id: uuid.UUID,
    label_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: IssueService = Depends(get_issue_service),
) -> IssueResponse:
    """Add a label to an issue (idempotent)."""
    log_action("add_label")
    log_entity("issue", issue_id)
    result = await service.add_label(issue_id, label_id, user_id=user_id)
    return IssueResponse.model_validate(result)


@issues_router.delete(
    "/{issue_id}/labels/{label_id}",
    response_description="Remove a label from an issue",
    status_code=status.HTTP_200_OK,
)
async def remove_label(
    issue_id: uuid.UUID,
    label_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: IssueService = Depends(get_issue_service),
) -> IssueResponse:
    """Remove a label from an issue."""
    log_action("remove_label")
    log_entity("issue", issue_id)
    result = await service.remove_label(issue_id, label_id, user_id=user_id)
    return IssueResponse.model_validate(result)

"""Comment router — CRUD endpoints for issue discussion threads."""

import uuid
from typing import cast

from fastapi import APIRouter, Body, Depends, Query, status
from fastapi_pagination import Page, Params

from app.core.logging import log_action, log_entity
from app.modules.comments.dependencies import get_comment_service
from app.modules.comments.filters import CommentFilter
from app.modules.comments.schemas import (
    CommentCreate,
    CommentResponse,
    CommentUpdate,
)
from app.modules.comments.service import CommentService
from app.user.auth import require_current_user_id

comments_router = APIRouter(
    prefix="/comments",
    tags=["comments"],
    dependencies=[Depends(require_current_user_id)],
)


@comments_router.get(
    "",
    response_description="List comments",
    status_code=status.HTTP_200_OK,
)
async def list_comments(
    pagination: Params = Depends(),
    comment_filter: CommentFilter = Depends(),
    issue_id: uuid.UUID | None = Query(
        default=None,
        description="Restrict to comments on this issue (used by the drawer thread)",
    ),
    team_id: uuid.UUID | None = Query(
        default=None, description="Restrict to a single team"
    ),
    order_by: list[str] | None = Query(
        default=None,
        description="Sort fields (prefix '-' for desc, e.g. -created_at)",
    ),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: CommentService = Depends(get_comment_service),
) -> Page[CommentResponse]:
    """List comments for the authenticated user's teams.

    Supports filtering by ``issue_id`` (the comments thread on an issue — used by
    the issue drawer) and ``team_id``. Defaults to newest-first so the most
    recently created comment renders at the top (VAL-COMMENTS-001/003).
    """
    log_action("list")
    # Override the filter's order_by — FastAPI's Depends() doesn't parse
    # list[str] fields from query params, so we extract order_by via Query().
    if order_by is not None:
        comment_filter.order_by = order_by
    result = await service.get_all_paginated(
        pagination_params=pagination,
        entity_filter=comment_filter,
        user_id=user_id,
        issue_id=issue_id,
        team_id=team_id,
    )
    return cast(
        "Page[CommentResponse]",
        Page[CommentResponse].model_validate(
            {
                "items": [CommentResponse.model_validate(c) for c in result.items],
                "total": result.total,
                "page": result.page,
                "size": result.size,
                "pages": result.pages,
            }
        ),
    )


@comments_router.get(
    "/{comment_id}",
    response_description="Get comment by ID",
    status_code=status.HTTP_200_OK,
)
async def get_comment(
    comment_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: CommentService = Depends(get_comment_service),
) -> CommentResponse:
    """Get a comment by ID, enforcing the issue's team membership."""
    log_action("get")
    result = await service.get_by_id(comment_id, user_id=user_id)
    return CommentResponse.model_validate(result)


@comments_router.post(
    "",
    response_description="Create a comment",
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    comment: CommentCreate = Body(...),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: CommentService = Depends(get_comment_service),
) -> CommentResponse:
    """Create a comment on an issue (member or admin).

    The author is set to the authenticated user. A blank/whitespace-only body is
    rejected with 422 (VAL-COMMENTS-001, VAL-COMMENTS-002).
    """
    log_action("create")
    result = await service.create(comment, user_id=user_id)
    log_entity("comment", result.id)
    return CommentResponse.model_validate(result)


@comments_router.patch(
    "/{comment_id}",
    response_description="Update a comment",
    status_code=status.HTTP_200_OK,
)
async def update_comment(
    comment_id: uuid.UUID,
    comment: CommentUpdate = Body(...),
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: CommentService = Depends(get_comment_service),
) -> CommentResponse:
    """Edit a comment's body in place (author or team admin only).

    Updates the displayed text without duplicating or reloading the thread
    (VAL-COMMENTS-005, VAL-COMMENTS-008).
    """
    log_action("update")
    log_entity("comment", comment_id)
    result = await service.update(comment_id, comment, user_id=user_id)
    return CommentResponse.model_validate(result)


@comments_router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Delete a comment",
)
async def delete_comment(
    comment_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    service: CommentService = Depends(get_comment_service),
) -> None:
    """Delete a comment by ID (author or team admin).

    Removes it from the thread; other comments remain (VAL-COMMENTS-006,
    VAL-COMMENTS-008).
    """
    log_action("delete")
    log_entity("comment", comment_id)
    await service.delete(comment_id, user_id=user_id)

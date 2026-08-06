"""Teams router — CRUD endpoints for Team entity."""

import uuid

from fastapi import APIRouter, Body, Depends, status
from fastapi_pagination import Page, Params

from app.core.logging import log_action, log_entity
from app.modules.teams.dependencies import get_team_service
from app.modules.teams.filters import TeamFilter
from app.modules.teams.schemas import (
    TeamCreate,
    TeamListItemResponse,
    TeamResponse,
    TeamUpdate,
)
from app.modules.teams.service import TeamService
from app.user.auth import require_current_user_id

teams_router = APIRouter(
    prefix="/teams",
    tags=["teams"],
    dependencies=[Depends(require_current_user_id)],
)


@teams_router.get(
    "",
    response_description="List teams",
    status_code=status.HTTP_200_OK,
)
async def list_teams(
    pagination: Params = Depends(),
    team_filter: TeamFilter = Depends(),
    user_id: uuid.UUID = Depends(require_current_user_id),
    team_service: TeamService = Depends(get_team_service),
) -> Page[TeamListItemResponse]:
    """List teams the authenticated user is a member of.

    Each item is enriched with ``my_role`` — the requesting user's role in that
    team — so the SPA can gate role-based UI (writes for guests, admin-only
    actions for members) without a second request (VAL-CROSS-025).
    """
    log_action("list")
    result = await team_service.get_all_paginated(
        pagination_params=pagination,
        entity_filter=team_filter,
        user_id=user_id,
    )
    # The page is already scoped to the user's teams, so every item has a role.
    role_map = await team_service.get_role_map_for_user(user_id)
    return Page[TeamListItemResponse](
        items=[
            TeamListItemResponse(
                id=t.id,
                name=t.name,
                key=t.key,
                issue_sequence=t.issue_sequence,
                my_role=role_map[t.id],
            )
            for t in result.items
        ],
        total=result.total,
        page=result.page,
        size=result.size,
        pages=result.pages,
    )


@teams_router.get(
    "/{team_id}",
    response_description="Get team by ID",
    status_code=status.HTTP_200_OK,
)
async def get_team(
    team_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    team_service: TeamService = Depends(get_team_service),
) -> TeamResponse:
    """Get a team by ID, enforcing membership."""
    log_action("get")
    result = await team_service.get_by_id(team_id, user_id=user_id)
    return TeamResponse.model_validate(result)


@teams_router.post(
    "",
    response_description="Create a new team",
    status_code=status.HTTP_201_CREATED,
)
async def create_team(
    team: TeamCreate = Body(...),
    user_id: uuid.UUID = Depends(require_current_user_id),
    team_service: TeamService = Depends(get_team_service),
) -> TeamResponse:
    """Create a new team and add the creator as admin."""
    log_action("create")
    result = await team_service.create(team, user_id=user_id)
    log_entity("team", result.id)
    return TeamResponse.model_validate(result)


@teams_router.patch(
    "/{team_id}",
    response_description="Update a team",
    status_code=status.HTTP_200_OK,
)
async def update_team(
    team_id: uuid.UUID,
    team: TeamUpdate = Body(...),
    user_id: uuid.UUID = Depends(require_current_user_id),
    team_service: TeamService = Depends(get_team_service),
) -> TeamResponse:
    """Update an existing team (admin only)."""
    log_action("update")
    log_entity("team", team_id)
    result = await team_service.update(team_id, team, user_id=user_id)
    return TeamResponse.model_validate(result)


@teams_router.delete(
    "/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Delete a team",
)
async def delete_team(
    team_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    team_service: TeamService = Depends(get_team_service),
) -> None:
    """Delete a team by ID (admin only)."""
    log_action("delete")
    log_entity("team", team_id)
    await team_service.delete(team_id, user_id=user_id)

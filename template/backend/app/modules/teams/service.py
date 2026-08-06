"""Team service — business logic layer.

Enforces team scoping (a user only sees teams they are a member of) and
provides helpers used by all later domain modules to scope their queries by
the authenticated user's team memberships.
"""

import re
import uuid

from fastapi_filter.base.filter import BaseFilterModel
from fastapi_pagination import Page, Params
from pydantic import BaseModel
from sqlalchemy import select

from app.modules.teams.models import Team, TeamMembership, TeamRole
from app.modules.teams.repository import TeamMembershipRepository, TeamRepository
from app.modules.teams.schemas import TeamCreate, TeamMembershipCreate
from app.repositories.base_repository import QueryOptions
from app.repositories.exceptions import NotFoundError
from app.services.base_crud_service import BaseService


def _derive_key_from_name(name: str) -> str:
    """Derive a short uppercase alphanumeric key from a name.

    e.g. ``"Acme Corp"`` → ``"ACME"``, ``"Jo"`` → ``"JOX"`` (padded).
    """
    cleaned = re.sub(r"[^A-Za-z0-9]", "", name).upper()
    if len(cleaned) < 2:
        cleaned = cleaned.ljust(2, "X")
    return cleaned[:4]


class TeamService(BaseService[Team]):
    """Service for Team entity with team-membership-based scoping."""

    repo: TeamRepository
    membership_repo: TeamMembershipRepository

    def __init__(
        self,
        repo: TeamRepository,
        membership_repo: TeamMembershipRepository,
    ) -> None:
        self.repo = repo
        self.membership_repo = membership_repo

    # ------------------------------------------------------------------
    # Team-scoping helpers (used by all later domain modules)
    # ------------------------------------------------------------------

    async def get_team_ids_for_user(self, user_id: uuid.UUID) -> list[uuid.UUID]:
        """Return IDs of all teams the user is a member of."""
        memberships = await self.membership_repo.get_all(
            options=QueryOptions(
                base_query=select(TeamMembership).where(
                    TeamMembership.user_id == user_id
                )
            )
        )
        return [m.team_id for m in memberships]

    async def get_teams_for_user(self, user_id: uuid.UUID) -> list[Team]:
        """Return all Team objects the user is a member of."""
        team_ids = await self.get_team_ids_for_user(user_id)
        if not team_ids:
            return []
        return await self.repo.get_all(
            options=QueryOptions(base_query=select(Team).where(Team.id.in_(team_ids)))
        )

    async def get_membership(
        self, user_id: uuid.UUID, team_id: uuid.UUID
    ) -> TeamMembership | None:
        """Return the membership record for a user in a team, or None."""
        memberships = await self.membership_repo.get_all(
            options=QueryOptions(
                base_query=select(TeamMembership).where(
                    TeamMembership.user_id == user_id,
                    TeamMembership.team_id == team_id,
                )
            )
        )
        return memberships[0] if memberships else None

    # ------------------------------------------------------------------
    # Onboarding
    # ------------------------------------------------------------------

    async def create_default_team_for_user(
        self, user_id: uuid.UUID, display_name: str
    ) -> Team:
        """Create a default Team and an admin TeamMembership for a new user.

        Called from AuthService.register after user creation.
        """
        key = await self._generate_unique_key(display_name)
        team = await self.repo.create(
            TeamCreate(name=f"{display_name}'s Workspace", key=key)
        )
        await self.membership_repo.create(
            TeamMembershipCreate(user_id=user_id, team_id=team.id, role=TeamRole.admin)
        )
        return team

    async def _generate_unique_key(self, name: str) -> str:
        """Generate a unique team key, appending a numeric suffix on collision."""
        base = _derive_key_from_name(name)
        existing_keys: set[str] = set(
            await self.repo.get_all(
                options=QueryOptions(
                    base_query=select(Team.key).where(Team.key.like(f"{base}%"))
                )
            )
        )
        if base not in existing_keys:
            return base
        suffix = 2
        while f"{base}{suffix}" in existing_keys:
            suffix += 1
        return f"{base}{suffix}"

    # ------------------------------------------------------------------
    # CRUD (team-scoped)
    # ------------------------------------------------------------------

    def _assert_membership(self, team: Team, team_ids: list[uuid.UUID]) -> None:
        """Raise NotFoundError if the team is not in the user's team set."""
        if team.id not in team_ids:
            raise NotFoundError(detail=f"Team '{team.id}' not found")

    async def get_by_id(  # type: ignore[override]
        self, entity_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> Team:
        """Get a team by ID, enforcing membership."""
        team_ids = await self.get_team_ids_for_user(user_id)
        team = await self.repo.get(entity_id, raise_error=True)
        self._assert_membership(team, team_ids)
        return team

    async def get_all_paginated(  # type: ignore[override]
        self,
        pagination_params: Params,
        entity_filter: BaseFilterModel | None = None,
        *,
        user_id: uuid.UUID,
    ) -> Page[Team]:
        """List teams the user is a member of."""
        team_ids = await self.get_team_ids_for_user(user_id)
        base_query = select(Team).where(Team.id.in_(team_ids))
        opts = QueryOptions(base_query=base_query)
        return await self.repo.get_all_paginated(pagination_params, entity_filter, opts)

    async def create(  # type: ignore[override]
        self, entity: BaseModel, *, user_id: uuid.UUID
    ) -> Team:
        """Create a team and add the creator as admin."""
        team = await self.repo.create(entity)
        await self.membership_repo.create(
            TeamMembershipCreate(user_id=user_id, team_id=team.id, role=TeamRole.admin)
        )
        return team

    async def update(  # type: ignore[override]
        self, entity_id: uuid.UUID, entity: BaseModel, *, user_id: uuid.UUID
    ) -> Team:
        """Update a team, enforcing admin role."""
        await self._require_role(user_id, entity_id, TeamRole.admin)
        return await self.repo.update(entity_id, entity)

    async def delete(  # type: ignore[override]
        self, entity_id: uuid.UUID, *, user_id: uuid.UUID
    ) -> None:
        """Delete a team, enforcing admin role."""
        await self._require_role(user_id, entity_id, TeamRole.admin)
        await self.repo.delete(entity_id)

    # ------------------------------------------------------------------
    # Role helpers
    # ------------------------------------------------------------------

    async def _require_role(
        self, user_id: uuid.UUID, team_id: uuid.UUID, required_role: TeamRole
    ) -> TeamMembership:
        """Return the membership if the user has at least the required role, else 403/404.

        A non-member gets a 404 (team not found) to avoid leaking existence.
        """
        memberships = await self.membership_repo.get_all(
            options=QueryOptions(
                base_query=select(TeamMembership).where(
                    TeamMembership.user_id == user_id,
                    TeamMembership.team_id == team_id,
                )
            )
        )
        if not memberships:
            raise NotFoundError(detail=f"Team '{team_id}' not found")
        membership = memberships[0]
        role_order = {TeamRole.guest: 0, TeamRole.member: 1, TeamRole.admin: 2}
        if role_order[membership.role] < role_order[required_role]:
            raise NotFoundError(detail=f"Team '{team_id}' not found")
        return membership

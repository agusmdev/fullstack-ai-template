"""IssueDependency repository — data access layer.

Extends the generic ``SQLAlchemyRepository`` with:
  - ``get``: eager-loads the blocker/blocked issues via ``selectinload`` so the
    response can render reciprocal display without an N+1 or a lazy-load outside
    an async context (the base repo's INSERT RETURNING path does not populate
    relationships).
  - ``get_edges_for_team``: returns the ``(blocker_id, blocked_id)`` pairs for a
    team, used by the service's circular-dependency guard.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.modules.issue_dependencies.models import IssueDependency
from app.modules.issues.models import Issue
from app.repositories.exceptions import NotFoundError
from app.repositories.sql_repository import SQLAlchemyRepository


class IssueDependencyRepository(SQLAlchemyRepository[IssueDependency]):
    """Repository for IssueDependency entity."""

    model = IssueDependency

    async def get(
        self,
        entity_id: uuid.UUID,
        raise_error: bool = True,
        response_model: type | None = None,
    ) -> IssueDependency | None:
        """Get a dependency by ID, eager-loading both related issues.

        Uses ``populate_existing=True`` so the relationships are refreshed from
        the DB even when the row is already in the identity map (e.g. right
        after ``create`` issued an INSERT RETURNING that did not load them).
        """
        query = (
            select(IssueDependency)
            .options(
                selectinload(IssueDependency.blocker),
                selectinload(IssueDependency.blocked),
            )
            .where(IssueDependency.id == entity_id)
            .execution_options(populate_existing=True)
        )
        result = await self._session.execute(query)
        item = result.scalar_one_or_none()
        if item is None and raise_error:
            raise NotFoundError(detail=f"Dependency '{entity_id}' not found")
        return item

    async def get_edges_for_team(
        self, team_id: uuid.UUID
    ) -> list[tuple[uuid.UUID, uuid.UUID]]:
        """Return all ``(blocker_id, blocked_id)`` dependency pairs in a team.

        Used by the cycle guard to build the team's dependency graph. Joins to
        ``issue`` on the blocker side; since both endpoints are same-team
        (enforced on create), filtering by the blocker's team is sufficient.
        """
        stmt = (
            select(IssueDependency.blocker_id, IssueDependency.blocked_id)
            .join(Issue, Issue.id == IssueDependency.blocker_id)
            .where(Issue.team_id == team_id)
        )
        result = await self._session.execute(stmt)
        return [(row[0], row[1]) for row in result.all()]

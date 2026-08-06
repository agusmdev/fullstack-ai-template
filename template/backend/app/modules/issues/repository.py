"""Issue repository — data access layer.

Extends the generic ``SQLAlchemyRepository`` with:
  - ``allocate_identifier``: atomically increments ``team.issue_sequence`` and
    returns the new ``TEAM-NN`` identifier (concurrency-safe via row-level lock).
  - ``add_label`` / ``remove_label``: manage the ``issue_label`` association.
  - ``get``: eager-loads labels via ``selectinload`` to avoid N+1 on detail views.
"""

import uuid

from sqlalchemy import delete as sql_delete
from sqlalchemy import select
from sqlalchemy import update as sql_update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import selectinload

from app.modules.issues.models import Issue
from app.modules.labels.models import issue_label
from app.modules.teams.models import Team
from app.repositories.exceptions import NotFoundError
from app.repositories.sql_repository import SQLAlchemyRepository


class IssueRepository(SQLAlchemyRepository[Issue]):
    """Repository for Issue entity."""

    model = Issue

    async def get(
        self,
        entity_id: uuid.UUID,
        raise_error: bool = True,
        response_model: type | None = None,
    ) -> Issue | None:
        """Get an issue by ID, eager-loading labels via selectinload.

        Uses ``populate_existing=True`` so the labels collection is refreshed
        from the DB even when the issue is already in the identity map (e.g.
        right after create + attach_labels in the same request).
        """
        query = (
            select(Issue)
            .options(selectinload(Issue.labels))
            .where(Issue.id == entity_id)
            .execution_options(populate_existing=True)
        )
        result = await self._session.execute(query)
        item = result.scalar_one_or_none()
        if item is None and raise_error:
            raise NotFoundError(detail=f"Issue '{entity_id}' not found")
        return item

    async def allocate_identifier(self, team_id: uuid.UUID) -> str:
        """Atomically increment ``team.issue_sequence`` and return ``KEY-NN``.

        Uses ``UPDATE … SET issue_sequence = issue_sequence + 1 RETURNING key,
        issue_sequence``. The row-level lock acquired by the UPDATE is held until
        the surrounding transaction commits, so concurrent calls serialise and
        each receive a distinct, monotonically increasing number.

        Deliberately does **not** commit — the caller (``IssueService.create``)
        commits via ``repo.create`` so both the sequence increment and the issue
        INSERT succeed or roll back atomically.
        """
        stmt = (
            sql_update(Team)
            .where(Team.id == team_id)
            .values(issue_sequence=Team.issue_sequence + 1)
            .returning(Team.key, Team.issue_sequence)
        )
        result = await self._session.execute(stmt)
        row = result.one_or_none()
        if row is None:
            raise NotFoundError(detail=f"Team '{team_id}' not found")
        return f"{row.key}-{row.issue_sequence}"

    async def add_label(self, issue_id: uuid.UUID, label_id: uuid.UUID) -> None:
        """Insert an issue_label row (idempotent via ON CONFLICT DO NOTHING)."""
        stmt = (
            pg_insert(issue_label)
            .values(issue_id=issue_id, label_id=label_id)
            .on_conflict_do_nothing(index_elements=["issue_id", "label_id"])
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def remove_label(self, issue_id: uuid.UUID, label_id: uuid.UUID) -> None:
        """Delete an issue_label row."""
        stmt = sql_delete(issue_label).where(
            issue_label.c.issue_id == issue_id,
            issue_label.c.label_id == label_id,
        )
        await self._session.execute(stmt)
        await self._session.commit()

    async def attach_labels(
        self, issue_id: uuid.UUID, label_ids: list[uuid.UUID]
    ) -> None:
        """Bulk-insert issue_label rows for the given label IDs (idempotent)."""
        if not label_ids:
            return
        rows = [{"issue_id": issue_id, "label_id": lid} for lid in label_ids]
        stmt = (
            pg_insert(issue_label)
            .values(rows)
            .on_conflict_do_nothing(index_elements=["issue_id", "label_id"])
        )
        await self._session.execute(stmt)
        await self._session.commit()

"""Activity repository — data access layer.

Extends the generic ``SQLAlchemyRepository`` with an overridden ``get`` that
eager-loads the actor via ``selectinload`` so list/detail responses can
serialize the nested ``ActorBrief`` without an N+1 or a lazy-load outside an
async context (the base repo's INSERT RETURNING path does not populate
relationships).
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.modules.activity.models import Activity
from app.repositories.exceptions import NotFoundError
from app.repositories.sql_repository import SQLAlchemyRepository


class ActivityRepository(SQLAlchemyRepository[Activity]):
    """Repository for Activity entity."""

    model = Activity

    async def get(
        self,
        entity_id: uuid.UUID,
        raise_error: bool = True,
        response_model: type | None = None,
    ) -> Activity | None:
        """Get an activity by ID, eager-loading the actor via selectinload.

        Uses ``populate_existing=True`` so the actor relationship is refreshed
        from the DB even when the row is already in the identity map.
        """
        query = (
            select(Activity)
            .options(selectinload(Activity.actor))
            .where(Activity.id == entity_id)
            .execution_options(populate_existing=True)
        )
        result = await self._session.execute(query)
        item = result.scalar_one_or_none()
        if item is None and raise_error:
            raise NotFoundError(detail=f"Activity '{entity_id}' not found")
        return item

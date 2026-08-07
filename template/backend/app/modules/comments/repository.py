"""Comment repository — data access layer.

Extends the generic ``SQLAlchemyRepository`` with an overridden ``get`` that
eager-loads the author via ``selectinload`` so list/detail/create responses can
serialize the nested ``AuthorBrief`` without an N+1 or a lazy-load outside an
async context (the base repo's INSERT RETURNING path does not populate
relationships).
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.modules.comments.models import Comment
from app.repositories.exceptions import NotFoundError
from app.repositories.sql_repository import SQLAlchemyRepository


class CommentRepository(SQLAlchemyRepository[Comment]):
    """Repository for Comment entity."""

    model = Comment

    async def get(
        self,
        entity_id: uuid.UUID,
        raise_error: bool = True,
        response_model: type | None = None,
    ) -> Comment | None:
        """Get a comment by ID, eager-loading the author via selectinload.

        Uses ``populate_existing=True`` so the author relationship is refreshed
        from the DB even when the row is already in the identity map (e.g.
        right after ``create`` issued an INSERT RETURNING that did not load it).
        """
        query = (
            select(Comment)
            .options(selectinload(Comment.author))
            .where(Comment.id == entity_id)
            .execution_options(populate_existing=True)
        )
        result = await self._session.execute(query)
        item = result.scalar_one_or_none()
        if item is None and raise_error:
            raise NotFoundError(detail=f"Comment '{entity_id}' not found")
        return item

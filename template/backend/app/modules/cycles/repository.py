"""Cycle repository — data access layer."""

from app.modules.cycles.models import Cycle
from app.repositories.sql_repository import SQLAlchemyRepository


class CycleRepository(SQLAlchemyRepository[Cycle]):
    """Repository for Cycle entity."""

    model = Cycle

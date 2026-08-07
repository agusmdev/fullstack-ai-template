"""View repository — data access layer."""

from app.modules.views.models import View
from app.repositories.sql_repository import SQLAlchemyRepository


class ViewRepository(SQLAlchemyRepository[View]):
    """Repository for View entity."""

    model = View

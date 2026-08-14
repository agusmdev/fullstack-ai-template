"""Item repository - database access layer."""

from app.modules.items.models import Item
from app.repositories.sql_repository import SQLAlchemyRepository


class ItemRepository(SQLAlchemyRepository[Item]):
    """Repository for Item entity."""

    model = Item

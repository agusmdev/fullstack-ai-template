"""Item repository - database access layer."""

from app.modules.items.models import Item
from app.repositories.sql_repository import SQLAlchemyRepository


class ItemRepository(SQLAlchemyRepository[Item]):
    """Repository for Item entity.

    Inherits all CRUD operations from SQLAlchemyRepository:
    - get(entity_id)
    - get_all(filter, pagination)
    - create(entity)
    - update(entity_id, entity)
    - delete(entity_id)
    - create_many(entities)
    """

    model = Item

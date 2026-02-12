"""Item service - business logic layer."""

import uuid

from app.modules.items.models import Item
from app.modules.items.repository import ItemRepository
from app.repositories.exceptions import NotFoundError
from app.services.base_crud_service import BaseService


class ItemService(BaseService[Item]):
    """Service for Item entity.

    Inherits all CRUD operations from BaseService:
    - get_by_id(entity_id)
    - get_all(filter, pagination)
    - create(entity)
    - create_many(entities)
    - upsert(entity)
    - update(entity_id, entity)
    - delete(entity_id)
    """

    def __init__(self, repo: ItemRepository) -> None:
        self.repo = repo

    async def get_by_sku(self, sku: str) -> Item:
        """Get an item by SKU.

        Args:
            sku: The SKU to look up

        Returns:
            The item with the matching SKU

        Raises:
            NotFoundError: If no item with the SKU exists
        """
        item = await self.repo.get(sku, filter_field="sku", raise_error=False)  # type: ignore[arg-type]
        if not item:
            raise NotFoundError(detail=f"Item with SKU '{sku}' not found")
        return item

"""Item service - business logic layer."""

import uuid

from app.modules.items.models import Item
from app.modules.items.repository import ItemRepository
from app.repositories.exceptions import NotFoundError
from app.services.base_crud_service import BaseService


class ItemService(BaseService[Item]):
    """Service for Item entity. Handles SKU-based inventory lookups."""

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
        item = await self.repo.get_by_field("sku", sku, raise_error=False)
        if not item:
            raise NotFoundError(detail=f"Item with SKU '{sku}' not found")
        return item

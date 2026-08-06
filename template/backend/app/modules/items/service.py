"""Item service - business logic layer."""

import uuid

from fastapi_filter.base.filter import BaseFilterModel
from fastapi_pagination import Page, Params
from pydantic import BaseModel
from sqlalchemy import select

from app.modules.items.models import Item
from app.modules.items.repository import ItemRepository
from app.repositories.base_repository import QueryOptions
from app.repositories.exceptions import NotFoundError
from app.services.base_crud_service import BaseService


class ItemService(BaseService[Item]):
    """Service for Item entity. Handles SKU-based inventory lookups and ownership enforcement."""

    def __init__(self, repo: ItemRepository) -> None:
        self.repo = repo

    def _assert_ownership(self, item: Item, user_id: uuid.UUID) -> None:
        """Raise NotFoundError if the item does not belong to user_id."""
        if item.user_id != user_id:
            raise NotFoundError(detail=f"Item '{item.id}' not found")

    async def get_by_id(self, entity_id: uuid.UUID, *, user_id: uuid.UUID) -> Item:  # type: ignore[override]  # adds required user_id to enforce ownership (intentional Liskov narrowing)
        """Get an item by ID, enforcing ownership."""
        item = await self.repo.get(entity_id, raise_error=True)
        self._assert_ownership(item, user_id)
        return item

    async def get_by_sku(self, sku: str, *, user_id: uuid.UUID) -> Item:
        """Get an item by SKU, enforcing ownership."""
        item = await self.repo.get_by_field("sku", sku, raise_error=False)
        if not item:
            raise NotFoundError(detail=f"Item with SKU '{sku}' not found")
        self._assert_ownership(item, user_id)
        return item

    async def get_all_paginated(  # type: ignore[override]  # adds required user_id to scope the list by ownership (intentional Liskov narrowing)
        self,
        pagination_params: Params,
        entity_filter: BaseFilterModel | None = None,
        *,
        user_id: uuid.UUID,
    ) -> Page[Item]:
        """List items, scoped to the requesting user."""
        base_query = select(Item).where(Item.user_id == user_id)
        opts = QueryOptions(base_query=base_query)
        return await self.repo.get_all_paginated(pagination_params, entity_filter, opts)

    async def create(self, entity: BaseModel, *, user_id: uuid.UUID) -> Item:  # type: ignore[override]  # narrows **extra_fields to required user_id (intentional Liskov narrowing)
        """Create an item bound to the requesting user."""
        return await super().create(entity, user_id=user_id)

    async def update(
        self, entity_id: uuid.UUID, entity: BaseModel, *, user_id: uuid.UUID
    ) -> Item:  # type: ignore[override]  # adds required user_id to enforce ownership (intentional Liskov narrowing)
        """Update an item, enforcing ownership."""
        item = await self.repo.get(entity_id, raise_error=True)
        self._assert_ownership(item, user_id)
        return await super().update(entity_id, entity)

    async def delete(self, entity_id: uuid.UUID, *, user_id: uuid.UUID) -> None:  # type: ignore[override]  # adds required user_id to enforce ownership (intentional Liskov narrowing)
        """Delete an item, enforcing ownership."""
        item = await self.repo.get(entity_id, raise_error=True)
        self._assert_ownership(item, user_id)
        await super().delete(entity_id)

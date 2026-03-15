"""Items router - CRUD endpoints for Item entity."""

import uuid
from typing import TYPE_CHECKING, cast

from fastapi import APIRouter, Body, Depends, status
from fastapi_pagination import Page, Params

from app.core.logging import log_action, log_entity
from app.user.auth.permissions import AuthenticatedUser
from app.modules.items.dependencies import get_item_service
from app.modules.items.filters import ItemFilter
from app.modules.items.schemas import ItemCreate, ItemResponse, ItemUpdate
from app.modules.items.service import ItemService

if TYPE_CHECKING:
    from app.modules.items.models import Item

items_router = APIRouter(
    prefix="/items",
    tags=["items"],
    dependencies=[Depends(AuthenticatedUser.current_user_id)],
)


@items_router.get(
    "",
    response_description="List items",
    status_code=status.HTTP_200_OK,
)
async def list_items(
    pagination: Params = Depends(),
    item_filter: ItemFilter = Depends(),
    item_service: ItemService = Depends(get_item_service),
) -> Page[ItemResponse]:
    """List all items with optional filtering and pagination.

    Query parameters:
        - page: Page number (default: 1)
        - size: Page size (default: 50)
        - search: Search in name, description, sku
        - name__like: Filter by name pattern
        - sku__eq: Filter by exact SKU
        - quantity__gte: Filter by minimum quantity
    """
    log_action("list")
    result: Page[Item] | list[Item] = await item_service.get_all(
        entity_filter=item_filter,
        pagination_params=pagination,
    )
    return cast("Page[ItemResponse]", result)


@items_router.get(
    "/{item_id}",
    response_description="Get item by ID",
    status_code=status.HTTP_200_OK,
)
async def get_item(
    item_id: uuid.UUID,
    item_service: ItemService = Depends(get_item_service),
) -> ItemResponse:
    """Get an item by ID."""
    log_action("get")
    log_entity("item", item_id)
    result = await item_service.get_by_id(item_id)
    return cast("ItemResponse", result)


@items_router.get(
    "/by-sku/{sku}",
    response_description="Get item by SKU",
    status_code=status.HTTP_200_OK,
)
async def get_item_by_sku(
    sku: str,
    item_service: ItemService = Depends(get_item_service),
) -> ItemResponse:
    """Get an item by SKU (custom endpoint example)."""
    log_action("get_by_sku")
    result = await item_service.get_by_sku(sku)
    log_entity("item", result.id)
    return cast("ItemResponse", result)


@items_router.post(
    "",
    response_description="Create a new item",
    status_code=status.HTTP_201_CREATED,
)
async def create_item(
    item: ItemCreate = Body(...),
    item_service: ItemService = Depends(get_item_service),
) -> ItemResponse:
    """Create a new item."""
    log_action("create")
    result = await item_service.create(item)
    log_entity("item", result.id)
    return cast("ItemResponse", result)


@items_router.patch(
    "/{item_id}",
    response_description="Update an item",
    status_code=status.HTTP_200_OK,
)
async def update_item(
    item_id: uuid.UUID,
    item: ItemUpdate = Body(...),
    item_service: ItemService = Depends(get_item_service),
) -> ItemResponse:
    """Update an existing item."""
    log_action("update")
    log_entity("item", item_id)
    return cast("ItemResponse", await item_service.update(item_id, item))


@items_router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Delete an item",
)
async def delete_item(
    item_id: uuid.UUID,
    item_service: ItemService = Depends(get_item_service),
) -> None:
    """Delete an item by ID."""
    log_action("delete")
    log_entity("item", item_id)
    await item_service.delete(item_id)

"""Items router - CRUD endpoints for Item entity."""

import uuid
from typing import cast

from fastapi import APIRouter, Body, Depends, status
from fastapi_pagination import Page, Params

from app.core.logging import log_action, log_entity
from app.modules.items.dependencies import get_item_service
from app.modules.items.filters import ItemFilter
from app.modules.items.schemas import ItemCreate, ItemResponse, ItemUpdate
from app.modules.items.service import ItemService
from app.user.auth import require_current_user_id

items_router = APIRouter(
    prefix="/items",
    tags=["items"],
    dependencies=[Depends(require_current_user_id)],
)


@items_router.get(
    "",
    response_description="List items",
    status_code=status.HTTP_200_OK,
)
async def list_items(
    pagination: Params = Depends(),
    item_filter: ItemFilter = Depends(),
    user_id: uuid.UUID = Depends(require_current_user_id),
    item_service: ItemService = Depends(get_item_service),
) -> Page[ItemResponse]:
    """List items owned by the authenticated user with optional filtering and pagination.

    Query parameters:
        - page: Page number (default: 1)
        - size: Page size (default: 50)
        - search: Search in name, description, sku
        - name__like: Filter by name pattern
        - sku__eq: Filter by exact SKU
        - quantity__gte: Filter by minimum quantity
    """
    log_action("list")
    result = await item_service.get_all_paginated(
        pagination_params=pagination,
        entity_filter=item_filter,
        user_id=user_id,
    )
    return cast("Page[ItemResponse]", result)


@items_router.get(
    "/{item_id}",
    response_description="Get item by ID",
    status_code=status.HTTP_200_OK,
)
async def get_item(
    item_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    item_service: ItemService = Depends(get_item_service),
) -> ItemResponse:
    """Get an item by ID, enforcing ownership."""
    log_action("get")
    result = await item_service.get_by_id(item_id, user_id=user_id)
    return cast("ItemResponse", result)


@items_router.get(
    "/by-sku/{sku}",
    response_description="Get item by SKU",
    status_code=status.HTTP_200_OK,
)
async def get_item_by_sku(
    sku: str,
    user_id: uuid.UUID = Depends(require_current_user_id),
    item_service: ItemService = Depends(get_item_service),
) -> ItemResponse:
    """Get an item by SKU (custom endpoint example), enforcing ownership."""
    log_action("get_by_sku")
    result = await item_service.get_by_sku(sku, user_id=user_id)
    log_entity("item", result.id)
    return cast("ItemResponse", result)


@items_router.post(
    "",
    response_description="Create a new item",
    status_code=status.HTTP_201_CREATED,
)
async def create_item(
    item: ItemCreate = Body(...),
    user_id: uuid.UUID = Depends(require_current_user_id),
    item_service: ItemService = Depends(get_item_service),
) -> ItemResponse:
    """Create a new item."""
    log_action("create")
    result = await item_service.create(item, user_id=user_id)
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
    user_id: uuid.UUID = Depends(require_current_user_id),
    item_service: ItemService = Depends(get_item_service),
) -> ItemResponse:
    """Update an existing item."""
    log_action("update")
    log_entity("item", item_id)
    return cast("ItemResponse", await item_service.update(item_id, item, user_id=user_id))


@items_router.delete(
    "/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Delete an item",
)
async def delete_item(
    item_id: uuid.UUID,
    user_id: uuid.UUID = Depends(require_current_user_id),
    item_service: ItemService = Depends(get_item_service),
) -> None:
    """Delete an item by ID."""
    log_action("delete")
    log_entity("item", item_id)
    await item_service.delete(item_id, user_id=user_id)

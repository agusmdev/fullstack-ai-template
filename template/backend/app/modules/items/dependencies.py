"""Dependency factory functions for Item module."""

from fastapi import Depends

from app.dependencies import get_repository
from app.modules.items.repository import ItemRepository
from app.modules.items.service import ItemService


def get_item_service(
    repo: ItemRepository = Depends(get_repository(ItemRepository)),
) -> ItemService:
    return ItemService(repo=repo)

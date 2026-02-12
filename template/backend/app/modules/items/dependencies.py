"""Dependency factory functions for Item module."""

from fastapi import Depends

from app.dependencies import get_repository
from app.modules.items.repository import ItemRepository
from app.modules.items.service import ItemService


def get_item_service(
    repo: ItemRepository = Depends(get_repository(ItemRepository)),
) -> ItemService:
    """Factory function to get ItemService instance.

    Args:
        repo: The ItemRepository instance (injected via Depends)

    Returns:
        ItemService: A service instance with the repository injected
    """
    return ItemService(repo=repo)

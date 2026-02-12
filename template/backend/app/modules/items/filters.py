"""Item filters - for filtering and searching items."""

from fastapi_filter.contrib.sqlalchemy.filter import Filter

from app.modules.items.models import Item


class ItemFilter(Filter):
    """Filter for Item queries.

    Usage in requests:
        ?search=keyword
        ?name__like=pattern
        ?sku__eq=ABC123
        ?quantity__gte=10
    """

    search: str | None = None

    class Constants(Filter.Constants):
        model = Item
        search_model_fields = ["name", "description"]

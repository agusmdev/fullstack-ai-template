"""Item filters - for filtering and searching items."""

from fastapi_filter.contrib.sqlalchemy.filter import Filter

from app.modules.items.models import Item


class ItemFilter(Filter):
    """Filter for Item queries.

    Usage in requests:
        ?search=keyword          (name or description, case-insensitive)
        ?name__ilike=%pattern%   (name only, case-insensitive)
        ?order_by=-created_at    (comma-separated; prefix "-" for descending)
    """

    order_by: list[str] = ["created_at"]
    name__ilike: str | None = None
    search: str | None = None

    class Constants(Filter.Constants):
        model = Item
        search_model_fields = ["name", "description"]

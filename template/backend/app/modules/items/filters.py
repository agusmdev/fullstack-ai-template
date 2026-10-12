"""Item filters - for filtering and searching items."""

from app.core.filters import ModelFilter
from app.modules.items.models import Item


class ItemFilter(ModelFilter):
    """Filter for Item queries.

    Usage in requests:
        ?search=keyword          (name or description, case-insensitive)
        ?name__ilike=%pattern%   (name only, case-insensitive)
        ?order_by=-created_at    (comma-separated; prefix "-" for descending)
    """

    order_by: list[str] = ["created_at"]
    name__ilike: str | None = None
    search: str | None = None

    class Constants(ModelFilter.Constants):
        model = Item
        search_model_fields = ["name", "description"]

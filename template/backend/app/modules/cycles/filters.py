"""Cycle filters — filtering, searching, and ordering for queries."""

from fastapi_filter.contrib.sqlalchemy.filter import Filter

from app.modules.cycles.models import Cycle


class CycleFilter(Filter):
    """Filter for Cycle queries.

    Usage in requests:
        ?search=keyword
        ?name__like=pattern
        ?order_by=-starts_at
    """

    order_by: list[str] = ["-created_at"]
    search: str | None = None
    name: str | None = None

    class Constants(Filter.Constants):
        model = Cycle
        search_model_fields = ["name"]

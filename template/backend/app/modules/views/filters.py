"""View filters — filtering, searching, and ordering for queries."""

from fastapi_filter.contrib.sqlalchemy.filter import Filter

from app.modules.views.models import View


class ViewFilter(Filter):
    """Filter for View queries.

    Usage in requests:
        ?search=keyword
        ?team_id=<uuid>
        ?order_by=name
    """

    order_by: list[str] = ["-created_at"]
    search: str | None = None
    team_id: str | None = None

    class Constants(Filter.Constants):
        model = View
        search_model_fields = ["name", "description"]

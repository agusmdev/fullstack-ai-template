"""Label filters — filtering, searching, and ordering for queries."""

from fastapi_filter.contrib.sqlalchemy.filter import Filter

from app.modules.labels.models import Label


class LabelFilter(Filter):
    """Filter for Label queries.

    Usage in requests:
        ?search=keyword
        ?name__like=pattern
        ?team_id__eq=<uuid>
        ?order_by=name
    """

    order_by: list[str] = ["name"]
    search: str | None = None

    class Constants(Filter.Constants):
        model = Label
        search_model_fields = ["name"]

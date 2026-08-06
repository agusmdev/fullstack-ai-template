"""Team filters — filtering and searching for team queries."""

from fastapi_filter.contrib.sqlalchemy.filter import Filter

from app.modules.teams.models import Team


class TeamFilter(Filter):
    """Filter for Team queries.

    Usage in requests:
        ?search=keyword
        ?name__like=pattern
        ?key__eq=ENG
        ?order_by=name
    """

    order_by: list[str] = ["created_at"]
    search: str | None = None

    class Constants(Filter.Constants):
        model = Team
        search_model_fields = ["name", "key"]

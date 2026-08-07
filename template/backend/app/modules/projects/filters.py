"""Project filters — filtering, searching, and ordering for queries."""

from fastapi_filter.contrib.sqlalchemy.filter import Filter

from app.modules.projects.models import Project


class ProjectFilter(Filter):
    """Filter for Project queries.

    Usage in requests:
        ?search=keyword
        ?name__like=pattern
        ?status=planned
        ?lead_id=<uuid>
        ?order_by=name
    """

    order_by: list[str] = ["-created_at"]
    search: str | None = None
    status: str | None = None
    lead_id: str | None = None

    class Constants(Filter.Constants):
        model = Project
        search_model_fields = ["name", "description"]

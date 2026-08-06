"""WorkflowState filters — filtering, searching, and ordering for queries."""

from fastapi_filter.contrib.sqlalchemy.filter import Filter

from app.modules.workflows.models import WorkflowState


class WorkflowStateFilter(Filter):
    """Filter for WorkflowState queries.

    Usage in requests:
        ?search=keyword
        ?name__like=pattern
        ?type__eq=started
        ?team_id__eq=<uuid>
        ?order_by=position
    """

    order_by: list[str] = ["position"]
    search: str | None = None

    class Constants(Filter.Constants):
        model = WorkflowState
        search_model_fields = ["name"]

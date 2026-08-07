"""Activity filters — ordering only.

Filtering by issue/team is handled in the service (those predicates join to
``issue``). Sorting defaults to newest-first so the most recent activity renders
at the top of the feed (VAL-ACTIVITY-001, VAL-ACTIVITY-008).
"""

from fastapi_filter.contrib.sqlalchemy.filter import Filter

from app.modules.activity.models import Activity


class ActivityFilter(Filter):
    """Filter for Activity queries."""

    order_by: list[str] = ["-created_at"]
    search: str | None = None

    class Constants(Filter.Constants):
        model = Activity
        search_model_fields = ["type"]

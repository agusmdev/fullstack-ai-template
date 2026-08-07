"""IssueDependency filters — ordering only.

Dependencies have no searchable text column of their own; filtering by issue or
team is handled in the service (those predicates join to ``issue``). Sorting
defaults to newest-first.
"""

from fastapi_filter.contrib.sqlalchemy.filter import Filter

from app.modules.issue_dependencies.models import IssueDependency


class IssueDependencyFilter(Filter):
    """Filter for IssueDependency queries."""

    order_by: list[str] = ["-created_at"]

    class Constants(Filter.Constants):
        model = IssueDependency

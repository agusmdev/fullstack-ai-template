"""Comment filters — ordering + body search.

Filtering by issue/team is handled in the service (those predicates join to
``issue``). Sorting defaults to newest-first (VAL-COMMENTS-001/003).
"""

from fastapi_filter.contrib.sqlalchemy.filter import Filter

from app.modules.comments.models import Comment


class CommentFilter(Filter):
    """Filter for Comment queries."""

    order_by: list[str] = ["-created_at"]
    search: str | None = None

    class Constants(Filter.Constants):
        model = Comment
        search_model_fields = ["body"]

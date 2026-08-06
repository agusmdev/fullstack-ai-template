"""Issue filters — filtering, searching, and ordering for queries.

Supports:
  - ``search``: case-insensitive substring match on title.
  - ``status_id``: exact match on workflow state.
  - ``priority``: exact match on priority (0–4).
  - ``assignee_id``: exact match on assignee.
  - ``order_by``: created_at, updated_at, priority (prefix ``-`` for desc).

Label filtering (``label_id``) is handled in the service via a subquery on
``issue_label`` since it is a many-to-many relationship, not a direct column.
"""

import uuid

from fastapi_filter.contrib.sqlalchemy.filter import Filter

from app.modules.issues.models import Issue


class IssueFilter(Filter):
    """Filter for Issue queries.

    Usage in requests:
        ?search=keyword
        ?status_id=<uuid>
        ?priority=0
        ?assignee_id=<uuid>
        ?order_by=-created_at
    """

    order_by: list[str] = ["-created_at"]
    search: str | None = None
    status_id: uuid.UUID | None = None
    priority: int | None = None
    assignee_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None

    class Constants(Filter.Constants):
        model = Issue
        search_model_fields = ["title"]

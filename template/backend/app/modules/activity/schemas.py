"""Activity schemas — response model (read-only).

Activity entries are **auto-generated** by ``IssueService`` on issue mutations
and exposed **read-only** (no create/update/delete endpoints) (VAL-ACTIVITY-009).
There is therefore no ``ActivityCreate``/``ActivityUpdate`` schema — the only
public schema is :class:`ActivityResponse`.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.database.mixins import OrmBaseModel


class ActorBrief(BaseModel):
    """Lightweight actor info embedded in an activity response.

    Carries just enough (id, display_name, email) for the SPA to render the
    actor of an activity entry without a second fetch (VAL-ACTIVITY-007).
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    display_name: str
    email: str


class ActivityResponse(OrmBaseModel):
    """Read-only activity entry with the nested actor brief.

    ``payload`` is the structured detail for the activity kind (from→to for a
    status change, the label name for a label add/remove, etc.) and is rendered
    verbatim by the SPA.
    """

    id: uuid.UUID
    issue_id: uuid.UUID
    actor_id: uuid.UUID
    type: str
    payload: dict[str, Any]
    actor: ActorBrief
    created_at: datetime

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=UTC), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        onupdate=lambda: datetime.now(tz=UTC),
        default=lambda: datetime.now(tz=UTC),
        index=True,
    )


class OrmBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

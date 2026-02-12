from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import JSONB
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


class JSONUpdatesMixing:
    updates_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")


class OrmBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class StrEnum(str, Enum):
    def __str__(self) -> str:
        return str.__str__(self)

    @classmethod
    def list(cls) -> list[str]:
        return [c.value for c in cls]


class TimestampOrmBaseModel(OrmBaseModel):
    created_at: datetime
    updated_at: datetime


class JsonOrmBaseModel(OrmBaseModel):
    updates_metadata: dict[str, datetime] = {}

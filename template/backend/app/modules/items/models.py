"""Item model - example entity for the template."""

import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TimestampMixin


class Item(TimestampMixin, Base):
    """Item model - example CRUD entity.

    This is a template example showing how to create a new entity
    in the app/modules/ directory. Follow this pattern for new entities.
    """

    __tablename__ = "item"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    quantity: Mapped[int] = mapped_column(default=0)
    sku: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)

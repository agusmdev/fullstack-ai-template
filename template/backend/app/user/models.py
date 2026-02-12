"""Module with the models for the DB connection for user"""

import uuid
from datetime import datetime

from argon2 import PasswordHasher
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.database.mixins import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(index=True, unique=True)
    display_name: Mapped[str] = mapped_column(index=True, server_default="")
    is_active: Mapped[bool] = mapped_column(default=True)

    password: Mapped[str | None] = mapped_column()
    email_verified_at: Mapped[datetime | None] = mapped_column(default=None)

    def check_password(self, password: str) -> bool:
        ph = PasswordHasher()
        if self.password is None:
            return False
        return ph.verify(self.password, password)

    @property
    def is_email_verified(self) -> bool:
        return self.email_verified_at is not None

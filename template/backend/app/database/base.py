from sqlalchemy import MetaData, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

meta = MetaData(
    naming_convention={
        "ix": "%(column_0_label)s_idx",
        "uq": "%(table_name)s_%(column_0_name)s_key",
        "ck": "%(table_name)s_%(constraint_name)s_check",
        "fk": "%(table_name)s_%(column_0_name)s_%(referred_table_name)s_fkey",
        "pk": "%(table_name)s_pkey",
    }
)


class Base(DeclarativeBase):
    metadata = meta

    @classmethod
    def _display_name(cls) -> str:
        return cls.__tablename__.capitalize()


def _convert_url_to_async(db_url: str) -> str:
    """Convert sync database URL to async.

    - postgres:// → postgresql+asyncpg://
    - postgresql:// → postgresql+asyncpg://
    - sqlite:// → sqlite+aiosqlite://
    """
    if db_url.startswith("postgres://"):
        return db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    if db_url.startswith("postgresql://"):
        return db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if db_url.startswith("sqlite://"):
        return db_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return db_url


def create_sqlalchemy_engine(*, db_url: str, pool_size: int) -> Engine:
    """Create sync SQLAlchemy engine (for Alembic migrations)."""
    return create_engine(
        db_url,
        pool_pre_ping=settings.DB_POOL_PRE_PING,
        echo=settings.DEBUG_MODE,
        pool_size=pool_size,
    )


def create_async_sqlalchemy_engine(*, db_url: str, pool_size: int) -> AsyncEngine:
    """Create async SQLAlchemy engine (for application use)."""
    async_url = _convert_url_to_async(db_url)
    return create_async_engine(
        async_url,
        pool_pre_ping=settings.DB_POOL_PRE_PING,
        echo=settings.DEBUG_MODE,
        pool_size=pool_size,
    )



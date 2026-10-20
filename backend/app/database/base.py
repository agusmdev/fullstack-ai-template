from sqlalchemy import MetaData
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


def _require_postgres_url(db_url: str) -> str:
    """Return the scheme-less rest of a Postgres URL; reject any other database.

    The template is Postgres-only (asyncpg for the app, psycopg for Alembic).
    """
    for scheme in ("postgres://", "postgresql://"):
        if db_url.startswith(scheme):
            return db_url.removeprefix(scheme)
    raise ValueError(
        "DB_URL must be a Postgres URL (postgresql://user:password@host:port/db)"
    )


def _convert_url_to_async(db_url: str) -> str:
    """Convert a plain Postgres URL to the asyncpg driver (postgresql+asyncpg://)."""
    if db_url.startswith("postgresql+asyncpg://"):
        return db_url
    return f"postgresql+asyncpg://{_require_postgres_url(db_url)}"


def _convert_url_to_sync(db_url: str) -> str:
    """Convert a plain Postgres URL to the psycopg driver (postgresql+psycopg://)."""
    if db_url.startswith("postgresql+psycopg://"):
        return db_url
    return f"postgresql+psycopg://{_require_postgres_url(db_url)}"


def create_async_sqlalchemy_engine(*, db_url: str, pool_size: int) -> AsyncEngine:
    """Create async SQLAlchemy engine (for application use).

    ``hide_parameters``: SQLAlchemy puts the bound values of a failed statement
    in the exception message (``[parameters: ...]``), and error logs include
    that message. The values are password hashes, tokens and user data.
    """
    async_url = _convert_url_to_async(db_url)
    return create_async_engine(
        async_url,
        pool_pre_ping=settings.DB_POOL_PRE_PING,
        echo=settings.DEBUG_MODE,
        pool_size=pool_size,
        hide_parameters=True,
    )

"""Dependency providers for FastAPI routes.

This module provides factory functions for database sessions and repositories,
designed for use with FastAPI's Depends() system.
"""

from collections.abc import AsyncGenerator, Awaitable, Callable
from functools import lru_cache
from typing import Protocol, TypeVar

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.database.base import Base, create_async_sqlalchemy_engine

T = TypeVar("T", bound=Base)


class RepositoryProtocol(Protocol):
    """Protocol for repository types that can be created with AsyncSession."""

    def __init__(self, session: AsyncSession) -> None: ...


R = TypeVar("R", bound=RepositoryProtocol)


@lru_cache
def get_engine() -> AsyncEngine:
    """Get the async database engine (singleton).

    Uses lru_cache to ensure only one engine is created per process.
    The engine is created with settings from the configuration.

    Returns:
        AsyncEngine: The async SQLAlchemy engine.
    """
    return create_async_sqlalchemy_engine(
        db_url=settings.DB_URL,
        pool_size=settings.DB_POOL_SIZE,
    )


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession; commits on success, rolls back on error."""
    engine = get_engine()
    session_factory = async_sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_repository[R: RepositoryProtocol](
    repository_type: type[R],
) -> Callable[[], Awaitable[R]]:
    """Return a FastAPI dependency that instantiates repository_type with a db session."""

    async def _get_repository(session: AsyncSession = Depends(get_db_session)) -> R:
        return repository_type(session)

    return _get_repository

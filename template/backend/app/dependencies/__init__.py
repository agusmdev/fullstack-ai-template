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
    """Get a database session with automatic commit/rollback.

    This is a FastAPI dependency that yields an AsyncSession.
    The session will be committed on success or rolled back on error.

    Yields:
        AsyncSession: An async database session.

    Example:
        @app.get("/items")
        async def get_items(session: AsyncSession = Depends(get_db_session)):
            result = await session.execute(select(Item))
            return result.scalars().all()
    """
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
    """Factory function to create a repository dependency.

    This returns a callable that can be used with FastAPI's Depends()
    to get a repository instance.

    Args:
        repository_type: The repository class to instantiate.

    Returns:
        A callable that creates a repository instance.

    Example:
        # Define repository dependency
        ItemRepositoryDep = get_repository(ItemRepository)

        # Use in route
        @app.get("/items")
        async def get_items(repo: ItemRepositoryDep = Depends()):
            return await repo.get_all()
    """

    async def _get_repository(session: AsyncSession = Depends(get_db_session)) -> R:
        return repository_type(session)

    return _get_repository

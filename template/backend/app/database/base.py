from sqlalchemy import MetaData, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
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


class DatabaseResource:
    """Class to handle database connections and sessions.

    Uses async sessions for application use.
    Provides sync methods for migration support.
    """

    def __init__(self, engine: AsyncEngine) -> None:
        self.async_engine = engine
        self._session_factory = async_sessionmaker(
            bind=self.async_engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

    async def create_database(self) -> None:
        """Create all tables (async)."""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    def create_database_sync(self) -> None:
        """Create all tables (sync - for migrations)."""
        Base.metadata.create_all(self.async_engine.sync_engine)

    async def drop_database(self) -> None:
        """Drop all tables (async)."""
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    def drop_database_sync(self) -> None:
        """Drop all tables (sync - for migrations)."""
        Base.metadata.drop_all(self.async_engine.sync_engine)

    def get_session(self) -> AsyncSession:
        """Get a new async session."""
        return self._session_factory()

    async def __aenter__(self) -> AsyncSession:
        self._session = self.get_session()
        return self._session

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        if exc_type:
            await self._session.rollback()
        else:
            await self._session.commit()
        await self._session.close()

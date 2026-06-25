from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    pass


_engine = None
_session_factory = None


def _get_engine():
    global _engine, _session_factory
    if _engine is None:
        url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
        _engine = create_async_engine(url, echo=False)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_session():
    """Return a new async session context manager. Safe to call from background tasks."""
    _get_engine()
    return _session_factory()


async def get_db() -> AsyncSession:
    async with get_session() as session:
        yield session

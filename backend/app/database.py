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
        _engine = create_async_engine(url, echo=settings.environment == "development")
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


async def get_db() -> AsyncSession:
    _get_engine()
    async with _session_factory() as session:
        yield session

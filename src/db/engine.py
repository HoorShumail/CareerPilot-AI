from typing import AsyncGenerator
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.config.settings import settings


def clean_asyncpg_uri(uri: str) -> str:
    """
    Remove query parameters that asyncpg does not support.
    """
    parsed = urlparse(uri)
    query = dict(parse_qsl(parsed.query))

    # Remove libpq-only parameters
    query.pop("sslmode", None)
    query.pop("channel_binding", None)

    return urlunparse(
        parsed._replace(query=urlencode(query))
    )


DATABASE_URL = clean_asyncpg_uri(settings.async_database_uri)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    connect_args={"ssl": "require"},
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
    echo=True,
)

# Create session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
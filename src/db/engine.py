from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.settings import settings

# Create async engine
engine = create_async_engine(
    settings.async_database_uri,
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10,
    echo=True,
)

# Create session factory
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database session"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

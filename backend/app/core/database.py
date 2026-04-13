from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

from sqlalchemy import pool
import asyncpg

async def async_creator():
    """Manual creator to ensure statement_cache_size is set early for pgBouncer."""
    return await asyncpg.connect(
        settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1),
        statement_cache_size=0,
        max_cached_statement_lifetime=0,
        ssl="require"
    )

engine = create_async_engine(
    settings.DATABASE_URL,
    async_creator=async_creator,
    echo=False,
    future=True,
    poolclass=pool.NullPool,    # Disable internal pooling for pgBouncer efficiency
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=True,  # Refresh state after commits
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

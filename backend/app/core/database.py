from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    # Connection pool configuration
    pool_size=settings.DB_POOL_SIZE,                    # Connections to keep in pool
    max_overflow=settings.DB_MAX_OVERFLOW,              # Additional peak connections
    pool_timeout=settings.DB_POOL_TIMEOUT,              # Fail fast on timeout
    pool_pre_ping=True,                                  # Health check before use
    pool_recycle=settings.DB_POOL_RECYCLE,              # Recycle stale connections
    pool_reset_on_return="rollback",                    # Clean state after use
    # Query optimization
    connect_args={
        "ssl": "require",
        "command_timeout": 30,
        "statement_cache_size": 0,                      # Disable statement caching (prepared statements)
        "prepared_statement_cache_size": 0,
        "server_settings": {
            "application_name": "students_backend",
            "jit": "off",                               # Disable JIT for consistency
        }
    },
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

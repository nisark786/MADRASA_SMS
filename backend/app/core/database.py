from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    pool_size=10,              # Increased for concurrency
    max_overflow=20,           # Allow more temporary overflow
    pool_timeout=30,           # Wait up to 30s for a connection
    pool_pre_ping=False,       # Disabled pre-ping for speed (rely on pool_recycle)
    pool_recycle=1800,         # Recycle every 30 min instead of 5
    connect_args={
        "ssl": "require",
        "command_timeout": 60, # Statements time out after 60s
    },
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

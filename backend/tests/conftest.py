"""
Pytest configuration and fixtures for testing the Students Data Store API.
"""
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from unittest.mock import AsyncMock, patch

from app.core.database import Base, get_db
from app.core.config import settings
from app.core import redis_client as rc
from main import app
from app.models.user import User
from app.models.role import Role, UserRole
from app.models.permission import Permission, RolePermission
from app.core.security import hash_password, create_access_token


# Use in-memory SQLite for tests (fast)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def test_db(test_engine):
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session


@pytest.fixture
async def client(test_db):
    """Create test client with dependency override."""
    async def override_get_db():
        yield test_db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def admin_user(test_db):
    """Create test admin user."""
    admin_role = Role(name="admin", display_name="Administrator", can_delete=False)
    test_db.add(admin_role)
    
    admin_user = User(
        username="admin",
        email="admin@test.com",
        password_hash=hash_password("test123456"),
        first_name="Test",
        last_name="Admin",
        is_active=True,
    )
    test_db.add(admin_user)
    await test_db.flush()
    
    user_role = UserRole(user_id=admin_user.id, role_id=admin_role.id)
    test_db.add(user_role)
    
    await test_db.commit()
    
    return admin_user


@pytest.fixture
async def admin_token(admin_user):
    """Create JWT token for admin user."""
    return create_access_token({"sub": admin_user.id})


@pytest.fixture
async def mock_redis():
    """Mock Redis client for testing."""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    mock.incr = AsyncMock(return_value=1)
    mock.expire = AsyncMock(return_value=True)
    mock.ttl = AsyncMock(return_value=600)
    mock.exists = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Markers for organizing tests
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )

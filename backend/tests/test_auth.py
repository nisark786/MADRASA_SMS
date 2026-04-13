"""
Tests for authentication endpoints.
Critical path: login, refresh, logout
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import hash_password


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_db: AsyncSession):
    """Test successful login."""
    # Create test user
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("password123"),
        first_name="Test",
        last_name="User",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    
    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "test@example.com"
    assert "csrf_token" in data
    assert "permissions" in data


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, test_db: AsyncSession):
    """Test login with invalid credentials."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("password123"),
        first_name="Test",
        last_name="User",
        is_active=True,
    )
    test_db.add(user)
    await test_db.commit()
    
    # Try with wrong password
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"}
    )
    
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, test_db: AsyncSession):
    """Test login with inactive user."""
    user = User(
        username="testuser",
        email="test@example.com",
        password_hash=hash_password("password123"),
        first_name="Test",
        last_name="User",
        is_active=False,  # Inactive
    )
    test_db.add(user)
    await test_db.commit()
    
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with non-existent user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "password123"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, admin_user, admin_token):
    """Test logout clears cookies."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await client.post("/api/v1/auth/logout", headers=headers)
    
    assert response.status_code == 200
    assert "Logged out successfully" in response.json()["message"]
    
    # Check that cookies are cleared in response
    assert "access_token" in response.cookies or "Set-Cookie" in str(response.headers)


@pytest.mark.asyncio
async def test_logout_unauthorized(client: AsyncClient):
    """Test logout without token."""
    response = await client.post("/api/v1/auth/logout")
    
    # Should fail without auth
    assert response.status_code == 403 or response.status_code == 401

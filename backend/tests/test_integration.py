"""
Integration tests for end-to-end workflows.

Tests complete user journeys including:
- User registration with password policy validation
- Login with rate limiting and CSRF protection
- User management (CRUD operations)
- Role and permission management
- Student management workflows
"""
import pytest
from unittest.mock import patch
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.role import Role, UserRole
from app.models.permission import Permission, RolePermission
from app.models.student import Student
from app.core.security import hash_password, verify_password
from app.core.password_policy import PasswordPolicy


@pytest.mark.integration
class TestUserRegistrationWorkflow:
    """Test user registration and password policy enforcement."""
    
    async def test_register_user_with_valid_password(self, client: AsyncClient, admin_token: str, test_db: AsyncSession):
        """Test successful user registration with valid password."""
        response = await client.post(
            "/api/v1/users",
            json={
                "username": "newuser",
                "email": "newuser@test.com",
                "password": "SecurePass123!@#",
                "first_name": "John",
                "last_name": "Doe",
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 201
        assert response.json()["username"] == "newuser"
        assert response.json()["email"] == "newuser@test.com"
        
        # Verify user was created in DB
        result = await test_db.execute(
            select(User).where(User.email == "newuser@test.com")
        )
        user = result.scalar_one_or_none()
        assert user is not None
    
    async def test_register_user_with_weak_password_too_short(self, client: AsyncClient, admin_token: str):
        """Test registration fails with weak password (too short)."""
        response = await client.post(
            "/api/v1/users",
            json={
                "username": "newuser2",
                "email": "newuser2@test.com",
                "password": "Short1!",  # Only 7 characters, needs 12+
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 422  # Validation error
        error = response.json()["detail"][0]
        assert "12 characters" in str(error["msg"])
    
    async def test_register_user_with_weak_password_no_uppercase(self, client: AsyncClient, admin_token: str):
        """Test registration fails without uppercase letter."""
        response = await client.post(
            "/api/v1/users",
            json={
                "username": "newuser3",
                "email": "newuser3@test.com",
                "password": "weakpassword123!",  # No uppercase
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 422
        error = response.json()["detail"][0]
        assert "uppercase" in str(error["msg"]).lower()
    
    async def test_register_user_with_weak_password_no_special_char(self, client: AsyncClient, admin_token: str):
        """Test registration fails without special character."""
        response = await client.post(
            "/api/v1/users",
            json={
                "username": "newuser4",
                "email": "newuser4@test.com",
                "password": "WeakPassword123",  # No special character
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 422
        error = response.json()["detail"][0]
        assert "special character" in str(error["msg"]).lower()


@pytest.mark.integration
class TestLoginWithRateLimiting:
    """Test login workflow with rate limiting."""
    
    async def test_successful_login_flow(self, client: AsyncClient, admin_user: User, mock_redis):
        """Test complete successful login flow."""
        # Mock Redis client
        with patch("app.core.rate_limit.rc.redis_client", mock_redis):
            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": admin_user.email,
                    "password": "test123456",
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == admin_user.email
        assert "csrf_token" in data
    
    async def test_login_invalid_email(self, client: AsyncClient, mock_redis):
        """Test login with non-existent email."""
        with patch("app.core.rate_limit.rc.redis_client", mock_redis):
            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "nonexistent@test.com",
                    "password": "password123",
                }
            )
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]
    
    async def test_login_invalid_password(self, client: AsyncClient, admin_user: User, mock_redis):
        """Test login with incorrect password."""
        with patch("app.core.rate_limit.rc.redis_client", mock_redis):
            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": admin_user.email,
                    "password": "wrongpassword",
                }
            )
        
        assert response.status_code == 401


@pytest.mark.integration
class TestPasswordChangeWorkflow:
    """Test password change workflow."""
    
    async def test_change_password_successfully(
        self, client: AsyncClient, admin_user: User, admin_token: str, test_db: AsyncSession
    ):
        """Test successful password change."""
        response = await client.post(
            "/api/v1/users/change-password",
            json={
                "current_password": "test123456",
                "new_password": "NewPassword123!@",
                "confirm_password": "NewPassword123!@",
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 200
        assert "successfully" in response.json()["message"].lower()
        
        # Verify password was updated in DB
        result = await test_db.execute(
            select(User).where(User.id == admin_user.id)
        )
        updated_user = result.scalar_one_or_none()
        
        # Old password should not verify
        assert not verify_password("test123456", updated_user.password_hash)
        # New password should verify
        assert verify_password("NewPassword123!@", updated_user.password_hash)
    
    async def test_change_password_wrong_current_password(
        self, client: AsyncClient, admin_token: str
    ):
        """Test password change fails with wrong current password."""
        response = await client.post(
            "/api/v1/users/change-password",
            json={
                "current_password": "wrongpassword",
                "new_password": "NewPassword123!@",
                "confirm_password": "NewPassword123!@",
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 401
    
    async def test_change_password_weak_new_password(
        self, client: AsyncClient, admin_token: str
    ):
        """Test password change fails with weak new password."""
        response = await client.post(
            "/api/v1/users/change-password",
            json={
                "current_password": "test123456",
                "new_password": "weak123",  # Too short and no special char
                "confirm_password": "weak123",
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert response.status_code == 422


@pytest.mark.integration
class TestUserManagementWorkflow:
    """Test complete user management workflow."""
    
    async def test_list_users_requires_permission(self, client: AsyncClient):
        """Test listing users requires admin permission."""
        response = await client.get("/api/v1/users")
        assert response.status_code == 401  # No auth
    
    async def test_create_and_list_users(
        self, client: AsyncClient, admin_user: User, admin_token: str, test_db: AsyncSession
    ):
        """Test creating and listing users."""
        # Create a new user
        create_response = await client.post(
            "/api/v1/users",
            json={
                "username": "testuser",
                "email": "testuser@test.com",
                "password": "TestPass123!@#",
                "first_name": "Test",
                "last_name": "User",
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert create_response.status_code == 201
        new_user_id = create_response.json()["id"]
        
        # List users
        list_response = await client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert list_response.status_code == 200
        users = list_response.json()
        assert len(users) >= 2  # At least admin + new user
        assert any(u["id"] == new_user_id for u in users)
    
    async def test_update_user(
        self, client: AsyncClient, admin_user: User, admin_token: str, test_db: AsyncSession
    ):
        """Test updating user information."""
        # Create a user first
        create_response = await client.post(
            "/api/v1/users",
            json={
                "username": "updateuser",
                "email": "updateuser@test.com",
                "password": "UpdatePass123!@",
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        user_id = create_response.json()["id"]
        
        # Update the user
        update_response = await client.patch(
            f"/api/v1/users/{user_id}",
            json={
                "first_name": "Updated",
                "last_name": "Name",
                "is_active": False,
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert update_response.status_code == 200
        
        # Verify update in DB
        result = await test_db.execute(
            select(User).where(User.id == user_id)
        )
        updated = result.scalar_one_or_none()
        assert updated.first_name == "Updated"
        assert updated.last_name == "Name"
        assert updated.is_active == False


@pytest.mark.integration
class TestRoleAndPermissionWorkflow:
    """Test role and permission management workflows."""
    
    async def test_create_role_with_permissions(
        self, client: AsyncClient, admin_user: User, admin_token: str, test_db: AsyncSession
    ):
        """Test creating a role with permissions."""
        # Create permissions first
        perm_response = await client.post(
            "/api/v1/permissions",
            json={
                "code": "test:read",
                "description": "Can read test data",
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        perm_id = perm_response.json()["id"]
        
        # Create role with permissions
        role_response = await client.post(
            "/api/v1/roles",
            json={
                "name": "tester",
                "display_name": "Tester Role",
                "permission_ids": [perm_id],
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert role_response.status_code == 201
        assert role_response.json()["name"] == "tester"


@pytest.mark.integration
class TestStudentManagementWorkflow:
    """Test student management workflows."""
    
    async def test_create_and_read_student(
        self, client: AsyncClient, admin_user: User, admin_token: str, test_db: AsyncSession
    ):
        """Test creating and reading a student."""
        # Create student
        create_response = await client.post(
            "/api/v1/students",
            json={
                "admission_no": "ADM001",
                "name": "John Doe",
                "class_name": "Grade 10",
                "email": "john@school.com",
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert create_response.status_code == 201
        student_id = create_response.json()["id"]
        
        # Read student
        get_response = await client.get(
            f"/api/v1/students/{student_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "John Doe"
        assert get_response.json()["admission_no"] == "ADM001"


@pytest.mark.integration
class TestCompleteUserJourney:
    """Test complete user journey from registration to logout."""
    
    async def test_full_user_lifecycle(
        self, client: AsyncClient, admin_user: User, admin_token: str, mock_redis, test_db: AsyncSession
    ):
        """Test complete user journey."""
        # Step 1: Create new user
        create_response = await client.post(
            "/api/v1/users",
            json={
                "username": "journeyuser",
                "email": "journey@test.com",
                "password": "JourneyPass123!@",
                "first_name": "Journey",
                "last_name": "User",
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert create_response.status_code == 201
        
        # Step 2: User logs in
        with patch("app.core.rate_limit.rc.redis_client", mock_redis):
            login_response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "journey@test.com",
                    "password": "JourneyPass123!@",
                }
            )
        assert login_response.status_code == 200
        user_token = login_response.json()["access_token"]
        
        # Step 3: Get user profile
        me_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "journey@test.com"
        
        # Step 4: Change password
        change_response = await client.post(
            "/api/v1/users/change-password",
            json={
                "current_password": "JourneyPass123!@",
                "new_password": "NewJourneyPass123!@",
                "confirm_password": "NewJourneyPass123!@",
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert change_response.status_code == 200
        
        # Step 5: Logout
        logout_response = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert logout_response.status_code == 200
        
        # Step 6: Verify old token no longer works
        me_after_logout = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert me_after_logout.status_code == 401

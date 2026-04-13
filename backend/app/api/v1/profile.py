"""User profile management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional

from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.core.password_policy import PasswordPolicy
from app.core.email_service import EmailService
from app.core.audit import log_audit_task
from app.core import redis_client as rc
from app.models.user import User
from app.dependencies.auth import get_current_user

router = APIRouter(prefix="/auth", tags=["User Profile"])


class UserProfileResponse(BaseModel):
    """User profile response."""
    id: str
    username: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    is_active: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    """Update user profile information."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, v):
        """Validate name fields."""
        if v is not None and len(v.strip()) == 0:
            raise ValueError("Name cannot be empty")
        if v is not None and len(v) > 100:
            raise ValueError("Name cannot exceed 100 characters")
        return v.strip() if v else None


class ChangePasswordRequest(BaseModel):
    """Change password request."""
    current_password: str
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v):
        """Validate new password against policy."""
        is_valid, error_msg = PasswordPolicy.validate(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current user's profile information.
    
    Requires authentication.
    """
    # Fetch fresh user data from DB to ensure latest info
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserProfileResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat(),
    )


@router.patch("/profile")
async def update_profile(
    body: UpdateProfileRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update current user's profile information.
    
    Can update:
    - first_name
    - last_name
    - email (must be unique)
    
    Requires authentication.
    """
    # Fetch user from DB
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # If email is being changed, check uniqueness
    if body.email and body.email != user.email:
        result = await db.execute(
            select(User.id).where(User.email == body.email)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already in use")
        
        # Email is being changed, send verification email
        old_email = user.email
        user.email = body.email
        
        # TODO: In a production system with email verification, we'd send a verification email
        # For now, we'll just update it directly
        
        background_tasks.add_task(
            send_email_changed_notification,
            user.email,
            old_email,
            db
        )
    
    # Update profile fields
    if body.first_name is not None:
        user.first_name = body.first_name
    if body.last_name is not None:
        user.last_name = body.last_name
    
    await db.commit()
    
    # Invalidate user cache
    background_tasks.add_task(rc.invalidate_user_object, current_user.id)
    background_tasks.add_task(log_audit_task, current_user.id, "UPDATE_PROFILE", "users", current_user.id)
    
    return {
        "message": "Profile updated successfully",
        "user": UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
        )
    }


@router.patch("/profile/change-password")
async def change_password_profile(
    body: ChangePasswordRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change current user's password.
    
    Requires:
    - Current password verification
    - New password matching confirmation
    - New password passing security policy
    
    Requires authentication.
    """
    # Fetch user from DB to get password hash
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")
    
    # Check that new password is different from current
    if verify_password(body.new_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be different from current password")
    
    # Verify passwords match
    if body.new_password != body.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")
    
    # Update password
    new_hash = hash_password(body.new_password)
    user.password_hash = new_hash
    await db.commit()
    
    # Invalidate user cache to force re-login
    await rc.invalidate_user_object(current_user.id)
    
    # Log audit event
    background_tasks.add_task(log_audit_task, current_user.id, "CHANGE_PASSWORD", "users", current_user.id)
    
    # Send confirmation email
    background_tasks.add_task(send_password_changed_notification, user.email, user.first_name or user.username, db)
    
    return {"message": "Password changed successfully"}


async def send_email_changed_notification(new_email: str, old_email: str, db: AsyncSession):
    """Send notification email when user's email is changed."""
    try:
        email_service = EmailService()
        # Using welcome template as a generic notification
        await email_service.send_email(
            recipient_email=new_email,
            recipient_name="User",
            template_name="welcome",
            context={
                "app_name": "Students Data Store",
                "first_name": "User",
                "username": "your account",
                "message": f"Your email address has been changed from {old_email} to {new_email}. If you didn't make this change, please contact support immediately.",
            },
            db=db,
        )
    except Exception as e:
        from app.core.structured_logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Failed to send email changed notification: {str(e)}")


async def send_password_changed_notification(email: str, name: str, db: AsyncSession):
    """Send notification email when user's password is changed."""
    try:
        email_service = EmailService()
        await email_service.send_email(
            recipient_email=email,
            recipient_name=name,
            template_name="welcome",
            context={
                "app_name": "Students Data Store",
                "first_name": name,
                "username": name,
                "message": "Your password has been changed successfully. If you didn't make this change, please reset your password immediately.",
            },
            db=db,
        )
    except Exception as e:
        from app.core.structured_logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Failed to send password changed notification: {str(e)}")

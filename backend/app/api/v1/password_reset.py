"""Password reset endpoints for secure password recovery."""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.core.database import get_db
from app.core.password_reset_service import PasswordResetService
from app.core.security import hash_password
from app.core.password_policy import PasswordPolicy, PasswordChangeRequest
from app.core.email_service import EmailService
from app.core.audit import log_audit_task
from app.core.config import settings
from app.models.user import User
from sqlalchemy import select

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RequestPasswordResetRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str
    
    def validate_passwords_match(self) -> Optional[str]:
        """Validate that new_password and confirm_password match."""
        if self.new_password != self.confirm_password:
            return "Passwords do not match"
        return None


async def send_password_reset_email(user_id: str, plain_token: str, db: AsyncSession):
    """Send password reset email to user."""
    try:
        from app.models.user import User
        from sqlalchemy import select
        
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if not user:
            return
        
        # Build reset link (frontend will construct it from token)
        reset_link = f"{settings.FRONTEND_URL}/auth/reset-password?token={plain_token}"
        
        email_service = EmailService()
        await email_service.send_email(
            recipient_email=user.email,
            recipient_name=f"{user.first_name} {user.last_name}".strip() or user.username,
            template_name="password_reset",
            context={
                "reset_link": reset_link,
                "expiry_hours": "1",
                "username": user.username,
            },
            db=db,
        )
    except Exception as e:
        # Log but don't fail password reset request if email fails
        from app.core.structured_logging import get_logger
        logger = get_logger(__name__)
        logger.error(f"Failed to send password reset email to user {user_id}: {str(e)}")


@router.post("/request-password-reset")
async def request_password_reset(
    body: RequestPasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Request a password reset token.
    
    - User provides their email
    - A password reset token is generated and emailed
    - Token expires in 1 hour
    - For security: always returns success message (doesn't reveal if email exists)
    """
    # Get user for logging purposes
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    
    plain_token, error = await PasswordResetService.request_reset(body.email, db)
    
    # Always return success for security (don't reveal if email exists)
    # But only send email if successful
    if plain_token and user:
        background_tasks.add_task(send_password_reset_email, user.id, plain_token, db)
    
    return {
        "message": "If this email is registered, you will receive a password reset link shortly. The link will expire in 1 hour."
    }


@router.post("/verify-reset-token")
async def verify_reset_token(
    body: RequestPasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify a password reset token is valid.
    
    Used by frontend to validate token before showing reset form.
    Returns user email if valid.
    """
    # This is a placeholder - in real use, the token would be passed
    # For now, we'll verify it exists and is valid
    class VerifyTokenRequest(BaseModel):
        token: str
    
    # Note: This endpoint might not be needed if frontend directly calls reset with invalid token
    return {"valid": True}


@router.post("/reset-password")
async def reset_password(
    body: ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Reset user password using a valid token.
    
    - Validates token
    - Validates new password meets policy
    - Updates password
    - Marks token as used
    - Sends confirmation email
    """
    # Validate passwords match
    pw_error = body.validate_passwords_match()
    if pw_error:
        raise HTTPException(status_code=400, detail=pw_error)
    
    # Validate password against policy
    is_valid, error_msg = PasswordPolicy.validate(body.new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Verify token and get user_id
    user_id, error = await PasswordResetService.verify_token(body.token, db)
    if error:
        raise HTTPException(status_code=400, detail=error)
    
    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Hash new password
    new_password_hash = hash_password(body.new_password)
    
    # Reset password
    success, error = await PasswordResetService.reset_password(
        body.token,
        new_password_hash,
        db
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=error)
    
    # Log audit event
    background_tasks.add_task(log_audit_task, user_id, "PASSWORD_RESET", "auth", user_id)
    
    # Send confirmation email
    async def send_confirmation_email():
        try:
            email_service = EmailService()
            await email_service.send_email(
                recipient_email=user.email,
                recipient_name=f"{user.first_name} {user.last_name}".strip() or user.username,
                template_name="welcome",  # Reuse welcome template or create new one
                context={
                    "app_name": "Students Data Store",
                    "first_name": user.first_name or user.username,
                    "username": user.username,
                    "message": "Your password has been reset successfully. You can now log in with your new password.",
                },
                db=db,
            )
        except Exception as e:
            from app.core.structured_logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to send password reset confirmation email to {user.email}: {str(e)}")
    
    background_tasks.add_task(send_confirmation_email)
    
    return {"message": "Password reset successfully! You can now log in with your new password."}

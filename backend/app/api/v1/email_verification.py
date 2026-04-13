"""Email verification endpoints."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.core.email_verification_service import EmailVerificationService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["email-verification"])


class VerifyEmailRequest:
    """Request model for email verification."""
    token: str


class ResendVerificationEmailRequest:
    """Request model for resending verification email."""
    pass


@router.post("/verify-email/{token}")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verify user's email address using a verification token.
    
    Args:
        token: Email verification token from email link
        db: Database session
    
    Returns:
        dict: Success message and user info
    
    Raises:
        HTTPException: 400 if token is invalid or expired
    """
    try:
        service = EmailVerificationService()
        is_valid, message, user = service.verify_email_token(db, token)
        
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        return {
            "success": True,
            "message": message,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "email_verified": user.email_verified,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during email verification"
        )


@router.post("/resend-verification-email")
async def resend_verification_email(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Resend email verification email to current user.
    
    Args:
        current_user: Currently authenticated user
        db: Database session
    
    Returns:
        dict: Success message
    
    Raises:
        HTTPException: 400 if email already verified, 500 on error
    """
    try:
        service = EmailVerificationService()
        
        # Build verification URL
        verification_url = f"{settings.FRONTEND_URL}/auth/verify-email?token={{token}}"
        
        # Create new token and get it
        plain_token, _ = service.create_verification_token(db, current_user.id)
        verification_url = verification_url.replace("{token}", plain_token)
        
        # Send email
        recipient_name = f"{current_user.first_name} {current_user.last_name}".strip() or current_user.username
        success = service.send_verification_email(
            db,
            current_user,
            verification_url,
            recipient_name
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send verification email"
            )
        
        return {
            "success": True,
            "message": "Verification email sent successfully. Please check your inbox."
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resending verification email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while resending the verification email"
        )


@router.get("/email-status")
async def get_email_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's email verification status.
    
    Args:
        current_user: Currently authenticated user
        db: Database session
    
    Returns:
        dict: Email verification status
    """
    return {
        "email": current_user.email,
        "email_verified": current_user.email_verified,
    }

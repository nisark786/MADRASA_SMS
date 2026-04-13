"""Two-Factor Authentication (2FA) endpoints."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.core.two_factor_service import TwoFactorAuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth/2fa", tags=["2fa"])


class SetupTwoFARequest(BaseModel):
    """Request to initiate 2FA setup."""
    pass


class ConfirmTwoFARequest(BaseModel):
    """Request to confirm 2FA setup."""
    totp_code: str


class VerifyTwoFARequest(BaseModel):
    """Request to verify 2FA during login."""
    totp_code: str = None
    backup_code: str = None


class DisableTwoFARequest(BaseModel):
    """Request to disable 2FA."""
    password: str


@router.post("/setup")
async def setup_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiate 2FA setup by generating TOTP secret and QR code.
    
    Returns:
        dict: secret key and QR code image (base64)
    """
    try:
        service = TwoFactorAuthService()
        secret, qr_code = service.initiate_2fa_setup(db, current_user)
        
        return {
            "success": True,
            "secret": secret,
            "qr_code": qr_code,
            "message": "Scan the QR code with your authenticator app and enter the code to confirm"
        }
    except Exception as e:
        logger.error(f"Error setting up 2FA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup 2FA"
        )


@router.post("/setup/confirm")
async def confirm_2fa_setup(
    body: ConfirmTwoFARequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirm 2FA setup by verifying TOTP code.
    
    Args:
        body: Request with totp_code (6-digit code from authenticator)
    
    Returns:
        dict: success status and backup codes
    """
    try:
        # Validate TOTP code format
        if not body.totp_code or len(body.totp_code) != 6 or not body.totp_code.isdigit():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TOTP code must be 6 digits"
            )
        
        service = TwoFactorAuthService()
        success, backup_codes = service.confirm_2fa_setup(db, current_user, body.totp_code)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid TOTP code. Please try again."
            )
        
        return {
            "success": True,
            "message": "2FA setup confirmed successfully!",
            "backup_codes": backup_codes,
            "warning": "Save these backup codes in a secure location. You can use them to access your account if you lose your authenticator."
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming 2FA setup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm 2FA setup"
        )


@router.post("/verify")
async def verify_2fa(
    body: VerifyTwoFARequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify 2FA code during login.
    
    Args:
        body: Request with totp_code OR backup_code
    
    Returns:
        dict: verification result
    """
    try:
        if not body.totp_code and not body.backup_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either TOTP code or backup code is required"
            )
        
        service = TwoFactorAuthService()
        
        if body.totp_code:
            if len(body.totp_code) != 6 or not body.totp_code.isdigit():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="TOTP code must be 6 digits"
                )
            success = service.verify_totp_code(db, current_user, body.totp_code)
        else:
            success = service.verify_backup_code(db, current_user, body.backup_code)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid verification code"
            )
        
        return {
            "success": True,
            "message": "2FA verification successful"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying 2FA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify 2FA code"
        )


@router.post("/disable")
async def disable_2fa(
    body: DisableTwoFARequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disable 2FA for current user.
    
    Args:
        body: Request with password confirmation
    
    Returns:
        dict: success status
    """
    try:
        from app.core.security import verify_password
        
        # Verify password before disabling 2FA
        if not verify_password(body.password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password"
            )
        
        service = TwoFactorAuthService()
        success = service.disable_2fa(db, current_user)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is not enabled"
            )
        
        return {
            "success": True,
            "message": "2FA has been disabled"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling 2FA: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable 2FA"
        )


@router.get("/status")
async def get_2fa_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get 2FA status for current user.
    
    Returns:
        dict: 2FA status information
    """
    try:
        service = TwoFactorAuthService()
        status = service.get_2fa_status(db, current_user)
        
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        logger.error(f"Error getting 2FA status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get 2FA status"
        )

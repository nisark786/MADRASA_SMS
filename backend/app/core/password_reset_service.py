"""Password reset service for secure password recovery."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, timezone

from app.models.password_reset import PasswordResetToken
from app.models.user import User


class PasswordResetService:
    """Service for managing password reset tokens and recovery flow."""

    @staticmethod
    async def request_reset(email: str, db: AsyncSession) -> tuple[str | None, str | None]:
        """
        Request a password reset token for a user.
        
        Returns:
            (plain_token, error_message)
            - If successful: (token, None)
            - If failed: (None, error_message)
        """
        try:
            # Find user by email
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            
            if not user:
                # Don't reveal if email exists (security best practice)
                return None, "If this email is registered, you will receive a password reset link shortly"
            
            # Invalidate any existing tokens for this user
            await db.execute(
                delete(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
            )
            
            # Create new token
            plain_token, token_obj = PasswordResetToken.create_token(user.id)
            token_obj.id = f"prt_{user.id}_{datetime.now(timezone.utc).timestamp()}"
            
            db.add(token_obj)
            await db.commit()
            
            return plain_token, None
            
        except Exception as e:
            await db.rollback()
            return None, f"Error requesting password reset: {str(e)}"

    @staticmethod
    async def verify_token(token: str, db: AsyncSession) -> tuple[str | None, str | None]:
        """
        Verify a password reset token.
        
        Returns:
            (user_id, error_message)
            - If valid: (user_id, None)
            - If invalid: (None, error_message)
        """
        try:
            token_hash = PasswordResetToken.hash_token(token)
            
            # Find token
            result = await db.execute(
                select(PasswordResetToken).where(
                    PasswordResetToken.token_hash == token_hash
                )
            )
            token_obj = result.scalar_one_or_none()
            
            if not token_obj:
                return None, "Invalid or expired password reset link"
            
            if not token_obj.is_valid():
                return None, "This password reset link has expired. Please request a new one."
            
            return token_obj.user_id, None
            
        except Exception as e:
            return None, f"Error verifying token: {str(e)}"

    @staticmethod
    async def reset_password(token: str, new_password_hash: str, db: AsyncSession) -> tuple[bool, str | None]:
        """
        Reset user password using a valid token.
        
        Returns:
            (success, error_message)
        """
        try:
            # Verify token
            user_id, error = await PasswordResetService.verify_token(token, db)
            if error:
                return False, error
            
            # Update user password
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                return False, "User not found"
            
            user.password_hash = new_password_hash
            
            # Mark token as used
            token_hash = PasswordResetToken.hash_token(token)
            result = await db.execute(
                select(PasswordResetToken).where(
                    PasswordResetToken.token_hash == token_hash
                )
            )
            token_obj = result.scalar_one_or_none()
            if token_obj:
                token_obj.mark_used()
            
            await db.commit()
            return True, None
            
        except Exception as e:
            await db.rollback()
            return False, f"Error resetting password: {str(e)}"

    @staticmethod
    async def cleanup_expired_tokens(db: AsyncSession) -> int:
        """
        Delete expired tokens (cleanup task).
        
        Returns:
            Number of tokens deleted
        """
        try:
            now = datetime.now(timezone.utc)
            result = await db.execute(
                delete(PasswordResetToken).where(
                    PasswordResetToken.expires_at < now
                )
            )
            await db.commit()
            return result.rowcount
        except Exception as e:
            await db.rollback()
            return 0

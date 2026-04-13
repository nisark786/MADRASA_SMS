"""Password reset tokens for secure password recovery."""
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta, timezone
import secrets
import hashlib

from app.core.database import Base


class PasswordResetToken(Base):
    """
    Secure password reset tokens with expiration.
    
    - Tokens are hashed for storage (only hash stored in DB)
    - Each token has a 1-hour expiration
    - Tokens are single-use (invalidated after use or expiration)
    - One token per user at a time (old tokens invalidated when new one created)
    """
    __tablename__ = "password_reset_tokens"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)  # SHA256 hash of token
    is_used = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    used_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship
    user = relationship("User", back_populates="password_reset_tokens")

    @staticmethod
    def generate_token() -> str:
        """Generate a secure random token (32 bytes = 256 bits)."""
        return secrets.token_urlsafe(32)

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash token using SHA256."""
        return hashlib.sha256(token.encode()).hexdigest()

    @classmethod
    def create_token(cls, user_id: str) -> tuple[str, "PasswordResetToken"]:
        """
        Create a new password reset token for a user.
        Returns: (plain_token, token_object)
        """
        plain_token = cls.generate_token()
        token_hash = cls.hash_token(plain_token)
        
        token_obj = cls(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        return plain_token, token_obj

    def is_valid(self) -> bool:
        """Check if token is still valid (not used and not expired)."""
        now = datetime.now(timezone.utc)
        return (
            not self.is_used and
            self.expires_at > now
        )

    def mark_used(self) -> None:
        """Mark token as used."""
        self.is_used = True
        self.used_at = datetime.now(timezone.utc)

"""Two-Factor Authentication (2FA) models."""
import uuid
import secrets
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TwoFactorAuth(Base):
    """
    Two-Factor Authentication (2FA) configuration for users.
    
    Supports:
    - TOTP (Time-based One-Time Password) via authenticator apps
    - Backup codes for account recovery
    - 2FA setup and verification tracking
    """
    __tablename__ = "two_factor_auth"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # 2FA configuration
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    totp_secret: Mapped[str] = mapped_column(String(255), nullable=True)  # Secret key for TOTP
    backup_codes: Mapped[str] = mapped_column(Text, nullable=True)  # JSON-encoded list of backup codes
    
    # Setup tracking
    setup_initiated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    setup_completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Last verification
    last_verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationship
    user = relationship("User", back_populates="two_factor_auth")

    @staticmethod
    def generate_backup_code() -> str:
        """Generate a single backup code (8 alphanumeric characters)."""
        return secrets.token_hex(4).upper()

    @classmethod
    def generate_backup_codes(cls, count: int = 10) -> list[str]:
        """Generate a list of backup codes."""
        return [cls.generate_backup_code() for _ in range(count)]

    def get_backup_codes(self) -> list[str]:
        """Retrieve backup codes from JSON storage."""
        import json
        if not self.backup_codes:
            return []
        try:
            codes = json.loads(self.backup_codes)
            # Filter out used codes (those marked as None)
            return [code for code in codes if code is not None]
        except (json.JSONDecodeError, TypeError):
            return []

    def set_backup_codes(self, codes: list[str]) -> None:
        """Store backup codes as JSON."""
        import json
        self.backup_codes = json.dumps(codes)

    def use_backup_code(self, code: str) -> bool:
        """
        Use a backup code and mark it as used.
        
        Args:
            code: The backup code to use
        
        Returns:
            bool: True if code was valid and unused, False otherwise
        """
        import json
        
        if not self.backup_codes:
            return False
        
        try:
            codes = json.loads(self.backup_codes)
            if code in codes:
                # Mark as used by replacing with None
                codes[codes.index(code)] = None
                self.backup_codes = json.dumps(codes)
                self.updated_at = datetime.now(timezone.utc)
                return True
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
        
        return False

    def has_remaining_backup_codes(self) -> bool:
        """Check if user has any unused backup codes."""
        return len(self.get_backup_codes()) > 0


class TwoFactorAuditLog(Base):
    """Audit log for 2FA events."""
    __tablename__ = "two_factor_audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Event information
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # setup, verify, disable, backup_used, failed_attempt
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # success, failure
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Request details
    ip_address: Mapped[str] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[str] = mapped_column(String(500), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    
    # Relationship
    user = relationship("User")

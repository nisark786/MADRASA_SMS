"""Two-Factor Authentication (2FA) service."""
import logging
import json
import pyotp
import qrcode
from io import BytesIO
from base64 import b64encode
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.two_factor_auth import TwoFactorAuth, TwoFactorAuditLog
from app.core.email_service import EmailService

logger = logging.getLogger(__name__)


class TwoFactorAuthService:
    """Service for managing Two-Factor Authentication."""
    
    def __init__(self, email_service: EmailService = None):
        self.email_service = email_service or EmailService()
    
    def initiate_2fa_setup(self, db: Session, user: User) -> tuple[str, str]:
        """
        Initiate 2FA setup by generating TOTP secret and QR code.
        
        Args:
            db: Database session
            user: User to set up 2FA for
        
        Returns:
            tuple[str, str]: (secret, qr_code_base64)
        """
        try:
            # Generate TOTP secret
            secret = pyotp.random_base32()
            
            # Get or create 2FA config
            two_fa = db.query(TwoFactorAuth).filter(
                TwoFactorAuth.user_id == user.id
            ).first()
            
            if not two_fa:
                two_fa = TwoFactorAuth(
                    user_id=user.id,
                    totp_secret=secret,
                )
                db.add(two_fa)
            else:
                two_fa.totp_secret = secret
            
            two_fa.setup_initiated_at = datetime.now(timezone.utc)
            db.commit()
            
            # Generate QR code
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(
                name=user.email,
                issuer_name="Students Data Store"
            )
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            qr_code_base64 = b64encode(buffered.getvalue()).decode()
            
            logger.info(f"2FA setup initiated for user {user.id}")
            self._log_2fa_event(db, user.id, "setup", "success", "2FA setup initiated")
            
            return secret, qr_code_base64
            
        except Exception as e:
            logger.error(f"Error initiating 2FA setup: {e}")
            self._log_2fa_event(db, user.id, "setup", "failure", str(e))
            raise
    
    def confirm_2fa_setup(self, db: Session, user: User, totp_code: str) -> tuple[bool, list[str]]:
        """
        Confirm 2FA setup by verifying TOTP code and generating backup codes.
        
        Args:
            db: Database session
            user: User completing 2FA setup
            totp_code: 6-digit TOTP code from authenticator
        
        Returns:
            tuple[bool, list[str]]: (success, backup_codes)
        """
        try:
            two_fa = db.query(TwoFactorAuth).filter(
                TwoFactorAuth.user_id == user.id
            ).first()
            
            if not two_fa or not two_fa.totp_secret:
                logger.warning(f"No 2FA setup in progress for user {user.id}")
                self._log_2fa_event(db, user.id, "setup", "failure", "No setup in progress")
                return False, []
            
            # Verify TOTP code (allow ±1 time window for clock skew)
            totp = pyotp.TOTP(two_fa.totp_secret)
            if not totp.verify(totp_code, valid_window=1):
                logger.warning(f"Invalid TOTP code for user {user.id}")
                self._log_2fa_event(db, user.id, "setup", "failure", "Invalid TOTP code")
                return False, []
            
            # Generate backup codes
            backup_codes = TwoFactorAuth.generate_backup_codes(10)
            two_fa.backup_codes = json.dumps(backup_codes)
            
            # Enable 2FA
            two_fa.is_enabled = True
            two_fa.setup_completed_at = datetime.now(timezone.utc)
            two_fa.updated_at = datetime.now(timezone.utc)
            
            db.commit()
            
            logger.info(f"2FA setup confirmed for user {user.id}")
            self._log_2fa_event(db, user.id, "setup", "success", "2FA setup confirmed")
            
            # Send notification email
            self._send_2fa_enabled_email(user)
            
            return True, backup_codes
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error confirming 2FA setup: {e}")
            self._log_2fa_event(db, user.id, "setup", "failure", str(e))
            return False, []
    
    def verify_totp_code(self, db: Session, user: User, totp_code: str) -> bool:
        """
        Verify TOTP code during login.
        
        Args:
            db: Database session
            user: User to verify
            totp_code: 6-digit TOTP code
        
        Returns:
            bool: True if valid, False otherwise
        """
        try:
            two_fa = db.query(TwoFactorAuth).filter(
                TwoFactorAuth.user_id == user.id
            ).first()
            
            if not two_fa or not two_fa.is_enabled or not two_fa.totp_secret:
                logger.warning(f"2FA not enabled for user {user.id}")
                return False
            
            totp = pyotp.TOTP(two_fa.totp_secret)
            if not totp.verify(totp_code, valid_window=1):
                logger.warning(f"Invalid TOTP code for user {user.id}")
                self._log_2fa_event(db, user.id, "verify", "failure", "Invalid TOTP code")
                return False
            
            # Update verification tracking
            two_fa.last_verified_at = datetime.now(timezone.utc)
            two_fa.verification_count += 1
            db.commit()
            
            self._log_2fa_event(db, user.id, "verify", "success", "TOTP code verified")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying TOTP: {e}")
            self._log_2fa_event(db, user.id, "verify", "failure", str(e))
            return False
    
    def verify_backup_code(self, db: Session, user: User, backup_code: str) -> bool:
        """
        Verify backup code during login.
        
        Args:
            db: Database session
            user: User to verify
            backup_code: Backup code string
        
        Returns:
            bool: True if valid and used, False otherwise
        """
        try:
            two_fa = db.query(TwoFactorAuth).filter(
                TwoFactorAuth.user_id == user.id
            ).first()
            
            if not two_fa or not two_fa.is_enabled:
                logger.warning(f"2FA not enabled for user {user.id}")
                return False
            
            # Try to use backup code
            if not two_fa.use_backup_code(backup_code.upper()):
                logger.warning(f"Invalid backup code for user {user.id}")
                self._log_2fa_event(db, user.id, "verify", "failure", "Invalid backup code")
                return False
            
            # Update verification tracking
            two_fa.last_verified_at = datetime.now(timezone.utc)
            two_fa.verification_count += 1
            db.commit()
            
            self._log_2fa_event(db, user.id, "verify", "success", "Backup code used")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error verifying backup code: {e}")
            self._log_2fa_event(db, user.id, "verify", "failure", str(e))
            return False
    
    def disable_2fa(self, db: Session, user: User) -> bool:
        """
        Disable 2FA for a user.
        
        Args:
            db: Database session
            user: User to disable 2FA for
        
        Returns:
            bool: True if successful
        """
        try:
            two_fa = db.query(TwoFactorAuth).filter(
                TwoFactorAuth.user_id == user.id
            ).first()
            
            if not two_fa or not two_fa.is_enabled:
                logger.warning(f"2FA not enabled for user {user.id}")
                return False
            
            two_fa.is_enabled = False
            two_fa.totp_secret = None
            two_fa.backup_codes = None
            two_fa.updated_at = datetime.now(timezone.utc)
            
            db.commit()
            
            logger.info(f"2FA disabled for user {user.id}")
            self._log_2fa_event(db, user.id, "disable", "success", "2FA disabled")
            
            # Send notification email
            self._send_2fa_disabled_email(user)
            
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error disabling 2FA: {e}")
            self._log_2fa_event(db, user.id, "disable", "failure", str(e))
            return False
    
    def get_2fa_status(self, db: Session, user: User) -> dict:
        """
        Get 2FA status for a user.
        
        Args:
            db: Database session
            user: User to get status for
        
        Returns:
            dict: 2FA status information
        """
        two_fa = db.query(TwoFactorAuth).filter(
            TwoFactorAuth.user_id == user.id
        ).first()
        
        if not two_fa:
            return {
                "enabled": False,
                "backup_codes_remaining": 0,
                "last_verified_at": None,
                "verification_count": 0,
            }
        
        return {
            "enabled": two_fa.is_enabled,
            "backup_codes_remaining": len(two_fa.get_backup_codes()) if two_fa.is_enabled else 0,
            "last_verified_at": two_fa.last_verified_at.isoformat() if two_fa.last_verified_at else None,
            "verification_count": two_fa.verification_count,
        }
    
    def _log_2fa_event(
        self,
        db: Session,
        user_id: str,
        event_type: str,
        status: str,
        description: str = None,
        ip_address: str = None,
        user_agent: str = None,
    ) -> None:
        """Log 2FA event to audit log."""
        try:
            log = TwoFactorAuditLog(
                user_id=user_id,
                event_type=event_type,
                status=status,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            db.add(log)
            db.commit()
        except Exception as e:
            logger.error(f"Error logging 2FA event: {e}")
    
    def _send_2fa_enabled_email(self, user: User) -> bool:
        """Send email notification when 2FA is enabled."""
        try:
            from jinja2 import Template
            
            html_template = """
            <html>
                <head>
                    <style>
                        body { font-family: Arial, sans-serif; }
                        .container { max-width: 600px; margin: 0 auto; }
                        .header { background-color: #10b981; color: white; padding: 20px; text-align: center; }
                        .content { padding: 20px; }
                        .footer { font-size: 12px; color: #999; padding: 20px; text-align: center; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>✓ Two-Factor Authentication Enabled</h1>
                        </div>
                        <div class="content">
                            <p>Hello {{ user_name }},</p>
                            <p>Two-Factor Authentication (2FA) has been successfully enabled on your account.</p>
                            <p><strong>What this means:</strong></p>
                            <ul>
                                <li>Your account is now more secure</li>
                                <li>You'll need to enter a code from your authenticator app when logging in</li>
                                <li>You have backup codes saved for account recovery</li>
                            </ul>
                            <p style="font-size: 12px; color: #666;">If you didn't enable 2FA, please contact support immediately.</p>
                        </div>
                        <div class="footer">
                            <p>© Students Data Store. All rights reserved.</p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            text_template = """
Hello {{ user_name }},

Two-Factor Authentication (2FA) has been successfully enabled on your account.

What this means:
- Your account is now more secure
- You'll need to enter a code from your authenticator app when logging in
- You have backup codes saved for account recovery

If you didn't enable 2FA, please contact support immediately.

© Students Data Store. All rights reserved.
            """
            
            recipient_name = f"{user.first_name} {user.last_name}".strip() or user.username
            html_body = Template(html_template).render(user_name=recipient_name)
            text_body = Template(text_template).render(user_name=recipient_name)
            
            return self.email_service.send_email_sync(
                recipient_email=user.email,
                subject="Two-Factor Authentication Enabled - Students Data Store",
                body_html=html_body,
                body_text=text_body,
                recipient_name=recipient_name
            )
        except Exception as e:
            logger.error(f"Error sending 2FA enabled email: {e}")
            return False
    
    def _send_2fa_disabled_email(self, user: User) -> bool:
        """Send email notification when 2FA is disabled."""
        try:
            from jinja2 import Template
            
            html_template = """
            <html>
                <head>
                    <style>
                        body { font-family: Arial, sans-serif; }
                        .container { max-width: 600px; margin: 0 auto; }
                        .header { background-color: #ef4444; color: white; padding: 20px; text-align: center; }
                        .content { padding: 20px; }
                        .footer { font-size: 12px; color: #999; padding: 20px; text-align: center; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>✗ Two-Factor Authentication Disabled</h1>
                        </div>
                        <div class="content">
                            <p>Hello {{ user_name }},</p>
                            <p>Two-Factor Authentication (2FA) has been disabled on your account.</p>
                            <p><strong>Please note:</strong> Your account may be less secure without 2FA. We recommend re-enabling it soon.</p>
                            <p>If you didn't disable 2FA, please secure your account and contact support immediately.</p>
                        </div>
                        <div class="footer">
                            <p>© Students Data Store. All rights reserved.</p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            text_template = """
Hello {{ user_name }},

Two-Factor Authentication (2FA) has been disabled on your account.

Please note: Your account may be less secure without 2FA. We recommend re-enabling it soon.

If you didn't disable 2FA, please secure your account and contact support immediately.

© Students Data Store. All rights reserved.
            """
            
            recipient_name = f"{user.first_name} {user.last_name}".strip() or user.username
            html_body = Template(html_template).render(user_name=recipient_name)
            text_body = Template(text_template).render(user_name=recipient_name)
            
            return self.email_service.send_email_sync(
                recipient_email=user.email,
                subject="Two-Factor Authentication Disabled - Students Data Store",
                body_html=html_body,
                body_text=text_body,
                recipient_name=recipient_name
            )
        except Exception as e:
            logger.error(f"Error sending 2FA disabled email: {e}")
            return False

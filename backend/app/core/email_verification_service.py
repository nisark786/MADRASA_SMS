"""Email verification service for managing verification tokens."""
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.email_verification import EmailVerificationToken
from app.models.user import User
from app.core.email_service import EmailService

logger = logging.getLogger(__name__)


class EmailVerificationService:
    """Service for managing email verification tokens and verification process."""
    
    def __init__(self, email_service: EmailService = None):
        self.email_service = email_service or EmailService()
    
    def create_verification_token(self, db: Session, user_id: str) -> tuple[str, EmailVerificationToken]:
        """
        Create a new email verification token for a user.
        
        If a token already exists, invalidate it first.
        
        Args:
            db: Database session
            user_id: User ID to create token for
        
        Returns:
            tuple[str, EmailVerificationToken]: (plain_token, token_object)
        """
        try:
            # Invalidate any existing tokens for this user
            existing_token = db.query(EmailVerificationToken).filter(
                EmailVerificationToken.user_id == user_id
            ).first()
            
            if existing_token:
                existing_token.is_used = True
                db.commit()
            
            # Create new token
            plain_token, token_obj = EmailVerificationToken.create_token(user_id)
            db.add(token_obj)
            db.commit()
            db.refresh(token_obj)
            
            logger.info(f"Email verification token created for user {user_id}")
            return plain_token, token_obj
            
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Error creating verification token: {e}")
            raise
    
    def verify_email_token(self, db: Session, token: str) -> tuple[bool, str, User]:
        """
        Verify an email verification token.
        
        Args:
            db: Database session
            token: Plain token string from user
        
        Returns:
            tuple[bool, str, User]: (is_valid, message, user_object or None)
        """
        try:
            # Hash the token and look it up
            token_hash = EmailVerificationToken.hash_token(token)
            token_obj = db.query(EmailVerificationToken).filter(
                EmailVerificationToken.token_hash == token_hash
            ).first()
            
            if not token_obj:
                logger.warning("Email verification token not found")
                return False, "Invalid or expired verification link", None
            
            # Check if token is valid
            if not token_obj.is_valid():
                logger.warning(f"Email verification token invalid for user {token_obj.user_id}")
                return False, "Verification link has expired. Please request a new one.", None
            
            # Get user
            user = db.query(User).filter(User.id == token_obj.user_id).first()
            if not user:
                logger.error(f"User {token_obj.user_id} not found for verification")
                return False, "User not found", None
            
            # Mark token as used and user email as verified
            token_obj.mark_used()
            user.email_verified = True
            user.updated_at = datetime.now(timezone.utc)
            
            db.commit()
            
            logger.info(f"Email verified for user {user.id}")
            return True, "Email verified successfully!", user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error verifying email token: {e}")
            return False, "An error occurred during verification", None
    
    def send_verification_email(
        self,
        db: Session,
        user: User,
        verification_url: str,
        recipient_name: str = None
    ) -> bool:
        """
        Send email verification email to user.
        
        Args:
            db: Database session
            user: User object
            verification_url: Full URL for email verification link
            recipient_name: Name to display in email (optional, uses user first_name + last_name)
        
        Returns:
            bool: True if email sent successfully
        """
        try:
            if not recipient_name:
                recipient_name = f"{user.first_name} {user.last_name}".strip() or user.username
            
            # Render email template
            from jinja2 import Template
            
            html_template = """
            <html>
                <head>
                    <style>
                        body { font-family: Arial, sans-serif; }
                        .container { max-width: 600px; margin: 0 auto; }
                        .header { background-color: #4f46e5; color: white; padding: 20px; text-align: center; }
                        .content { padding: 20px; }
                        .button { background-color: #4f46e5; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; }
                        .footer { font-size: 12px; color: #999; padding: 20px; text-align: center; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>Email Verification</h1>
                        </div>
                        <div class="content">
                            <p>Hello {{ user_name }},</p>
                            <p>Thank you for registering with Students Data Store. Please verify your email address to complete your account setup.</p>
                            <p style="text-align: center; margin: 30px 0;">
                                <a href="{{ verification_url }}" class="button">Verify Email</a>
                            </p>
                            <p style="font-size: 14px;">Or copy this link in your browser:<br/>
                            <code style="background: #f0f0f0; padding: 10px; display: block; word-break: break-all;">{{ verification_url }}</code></p>
                            <p style="font-size: 12px; color: #999;">This link expires in 24 hours.</p>
                            <p style="font-size: 12px; color: #999;">If you didn't create this account, please ignore this email.</p>
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

Thank you for registering with Students Data Store. Please verify your email address to complete your account setup.

Verification Link:
{{ verification_url }}

This link expires in 24 hours.

If you didn't create this account, please ignore this email.

© Students Data Store. All rights reserved.
            """
            
            html_body = Template(html_template).render(user_name=recipient_name, verification_url=verification_url)
            text_body = Template(text_template).render(user_name=recipient_name, verification_url=verification_url)
            
            # Send email
            success = self.email_service.send_email_sync(
                recipient_email=user.email,
                subject="Verify Your Email Address - Students Data Store",
                body_html=html_body,
                body_text=text_body,
                recipient_name=recipient_name
            )
            
            if success:
                logger.info(f"Verification email sent to {user.email}")
            else:
                logger.error(f"Failed to send verification email to {user.email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending verification email: {e}")
            return False
    
    def resend_verification_email(
        self,
        db: Session,
        user: User,
        verification_url: str
    ) -> tuple[bool, str]:
        """
        Resend verification email to user.
        
        Args:
            db: Database session
            user: User object
            verification_url: Full URL for email verification link
        
        Returns:
            tuple[bool, str]: (success, message)
        """
        try:
            # Check if user is already verified
            if user.email_verified:
                return False, "Email is already verified"
            
            # Create a new token
            plain_token, _ = self.create_verification_token(db, user.id)
            
            # Update verification URL with new token
            verification_url = verification_url.replace("token=", f"token={plain_token}")
            
            # Send email
            recipient_name = f"{user.first_name} {user.last_name}".strip() or user.username
            success = self.send_verification_email(db, user, verification_url, recipient_name)
            
            if success:
                return True, "Verification email sent successfully"
            else:
                return False, "Failed to send verification email. Please try again."
            
        except Exception as e:
            logger.error(f"Error resending verification email: {e}")
            return False, f"An error occurred: {str(e)}"

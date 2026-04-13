"""
Email service for sending emails with templates.
Handles SMTP configuration, template rendering, and async email queue.
"""
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from jinja2 import Template
import logging

from app.core.config import settings
from app.models.email import Email, EmailStatus

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP."""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL
        self.from_name = settings.SMTP_FROM_NAME or "Students Data Store"
    
    def send_email_sync(
        self,
        recipient_email: str,
        subject: str,
        body_html: str,
        body_text: str = None,
        recipient_name: str = None,
    ) -> bool:
        """
        Send email synchronously via SMTP.
        
        Args:
            recipient_email: Email address to send to
            subject: Email subject
            body_html: HTML email body
            body_text: Plain text email body (optional)
            recipient_name: Recipient name (optional)
        
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = f"{recipient_name} <{recipient_email}>" if recipient_name else recipient_email
            
            # Attach plain text and HTML versions
            if body_text:
                msg.attach(MIMEText(body_text, "plain"))
            msg.attach(MIMEText(body_html, "html"))
            
            # Send via SMTP
            logger.info(f"Connecting to SMTP: {self.smtp_server}:{self.smtp_port}")
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {recipient_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False
    
    async def send_email_async(
        self,
        recipient_email: str,
        subject: str,
        body_html: str,
        body_text: str = None,
        recipient_name: str = None,
        db_session = None,
        email_type: str = None,
        related_user_id: str = None,
        related_entity_type: str = None,
        related_entity_id: str = None,
    ) -> bool:
        """
        Send email asynchronously and track in database.
        
        Args:
            recipient_email: Email address to send to
            subject: Email subject
            body_html: HTML email body
            body_text: Plain text email body (optional)
            recipient_name: Recipient name (optional)
            db_session: Database session for tracking email
            email_type: Type of email (for categorization)
            related_user_id: Related user ID (for reference)
            related_entity_type: Related entity type (for reference)
            related_entity_id: Related entity ID (for reference)
        
        Returns:
            True if sent successfully, False otherwise
        """
        # Create email record in database
        email_record = None
        if db_session:
            email_record = Email(
                recipient_email=recipient_email,
                recipient_name=recipient_name,
                subject=subject,
                body_html=body_html,
                body_text=body_text or "",
                status=EmailStatus.PENDING,
                email_type=email_type,
                related_user_id=related_user_id,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id,
            )
            db_session.add(email_record)
            await db_session.commit()
            logger.info(f"Email record created: {email_record.id}")
        
        # Send email in background
        try:
            success = await asyncio.to_thread(
                self.send_email_sync,
                recipient_email,
                subject,
                body_html,
                body_text,
                recipient_name,
            )
            
            if success and email_record and db_session:
                email_record.status = EmailStatus.SENT
                email_record.sent_at = datetime.now(timezone.utc)
                email_record.retry_count = 0
                await db_session.commit()
                logger.info(f"Email marked as sent: {email_record.id}")
            elif not success and email_record and db_session:
                email_record.status = EmailStatus.FAILED
                email_record.retry_count += 1
                email_record.error_message = "SMTP delivery failed"
                await db_session.commit()
                logger.error(f"Email marked as failed: {email_record.id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error in async email sending: {e}")
            if email_record and db_session:
                email_record.status = EmailStatus.FAILED
                email_record.error_message = str(e)
                email_record.retry_count += 1
                try:
                    await db_session.commit()
                except Exception as commit_error:
                    logger.error(f"Error updating email record: {commit_error}")
            return False


class EmailTemplateRenderer:
    """Service for rendering Jinja2 email templates."""
    
    @staticmethod
    def render_template(template_html: str, context: dict) -> str:
        """
        Render Jinja2 template with context.
        
        Args:
            template_html: Jinja2 template string
            context: Dictionary of variables for template
        
        Returns:
            Rendered HTML string
        """
        try:
            template = Template(template_html)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            return template_html  # Return original if rendering fails


# Pre-defined email templates
DEFAULT_EMAIL_TEMPLATES = [
    {
        "name": "welcome",
        "subject": "Welcome to {{ app_name }}",
        "body_html": """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Welcome to {{ app_name }}!</h2>
                <p>Hi {{ user_name }},</p>
                <p>Your account has been created successfully.</p>
                <p><strong>Email:</strong> {{ email }}</p>
                <p><strong>Temporary Password:</strong> {{ password }}</p>
                <p>Please change your password after first login.</p>
                <p>Best regards,<br/>The {{ app_name }} Team</p>
            </body>
        </html>
        """,
        "body_text": "Welcome to {{ app_name }}!\n\nHi {{ user_name }},\n\nYour account has been created. Email: {{ email }}\nTemporary Password: {{ password }}\n\nPlease change your password after first login."
    },
    {
        "name": "password_reset",
        "subject": "Password Reset Request - {{ app_name }}",
        "body_html": """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Password Reset Request</h2>
                <p>Hi {{ user_name }},</p>
                <p>We received a request to reset your password.</p>
                <p><a href="{{ reset_link }}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
                <p>This link expires in 1 hour.</p>
                <p>If you didn't request this, please ignore this email.</p>
                <p>Best regards,<br/>The {{ app_name }} Team</p>
            </body>
        </html>
        """,
        "body_text": "Password Reset Request\n\nHi {{ user_name }},\n\nReset your password: {{ reset_link }}\nThis link expires in 1 hour.\n\nIf you didn't request this, ignore this email."
    },
    {
        "name": "form_approved",
        "subject": "Form Submission Approved - {{ app_name }}",
        "body_html": """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Form Submission Approved</h2>
                <p>Hi {{ recipient_name }},</p>
                <p>Your form submission has been approved!</p>
                <p><strong>Form:</strong> {{ form_name }}</p>
                <p>You can now access your information in the system.</p>
                <p>Best regards,<br/>The {{ app_name }} Team</p>
            </body>
        </html>
        """,
        "body_text": "Form Submission Approved\n\nHi {{ recipient_name }},\n\nYour form: {{ form_name }} has been approved.\n\nBest regards,\nThe {{ app_name }} Team"
    },
    {
        "name": "form_rejected",
        "subject": "Form Submission - Action Required - {{ app_name }}",
        "body_html": """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Form Submission Requires Changes</h2>
                <p>Hi {{ recipient_name }},</p>
                <p>Your form submission could not be approved.</p>
                <p><strong>Form:</strong> {{ form_name }}</p>
                <p><strong>Reason:</strong> {{ rejection_reason }}</p>
                <p>Please resubmit the form with the required changes.</p>
                <p>Best regards,<br/>The {{ app_name }} Team</p>
            </body>
        </html>
        """,
        "body_text": "Form Submission - Action Required\n\nHi {{ recipient_name }},\n\nYour form: {{ form_name }} needs changes.\nReason: {{ rejection_reason }}\n\nPlease resubmit with required changes."
    },
    {
        "name": "email_verification",
        "subject": "Verify Your Email - {{ app_name }}",
        "body_html": """
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Verify Your Email Address</h2>
                <p>Hi {{ user_name }},</p>
                <p>Thank you for signing up. Please verify your email address.</p>
                <p><a href="{{ verification_link }}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
                <p>This link expires in 24 hours.</p>
                <p>Best regards,<br/>The {{ app_name }} Team</p>
            </body>
        </html>
        """,
        "body_text": "Verify Your Email Address\n\nHi {{ user_name }},\n\nVerify your email: {{ verification_link }}\nThis link expires in 24 hours."
    },
]


async def seed_email_templates(db_session):
    """
    Seed default email templates into database.
    Called during app startup.
    """
    from app.models.email import EmailTemplate
    
    try:
        for template_data in DEFAULT_EMAIL_TEMPLATES:
            existing = await db_session.execute(
                __import__('sqlalchemy').select(EmailTemplate).where(
                    EmailTemplate.name == template_data["name"]
                )
            )
            if not existing.scalar_one_or_none():
                template = EmailTemplate(**template_data)
                db_session.add(template)
        
        await db_session.commit()
        logger.info("Email templates seeded successfully")
    except Exception as e:
        logger.error(f"Error seeding email templates: {e}")

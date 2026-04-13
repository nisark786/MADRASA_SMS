"""
Email model for tracking sent emails and templates.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Enum, Integer
from sqlalchemy.orm import declarative_base
import enum
import uuid

Base = declarative_base()


class EmailStatus(str, enum.Enum):
    """Email sending status."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    BOUNCED = "bounced"


class Email(Base):
    """Email record for tracking sent emails."""
    __tablename__ = "emails"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    recipient_email = Column(String(255), nullable=False, index=True)
    recipient_name = Column(String(255), nullable=True)
    subject = Column(String(255), nullable=False)
    body_html = Column(Text, nullable=False)
    body_text = Column(Text, nullable=True)
    status = Column(Enum(EmailStatus), default=EmailStatus.PENDING, nullable=False)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    sent_at = Column(DateTime, nullable=True)
    
    # Email type for categorization
    email_type = Column(String(50), nullable=True)  # login_welcome, password_reset, form_approved, etc.
    
    # Reference to related entity (optional)
    related_user_id = Column(String, nullable=True, index=True)
    related_entity_type = Column(String(50), nullable=True)  # "student", "form", etc.
    related_entity_id = Column(String, nullable=True)

    def __repr__(self):
        return f"<Email(id={self.id}, recipient={self.recipient_email}, status={self.status})>"


class EmailTemplate(Base):
    """Email template for reusable email content."""
    __tablename__ = "email_templates"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False, index=True)  # welcome, password_reset, form_approved, etc.
    subject = Column(String(255), nullable=False)
    body_html = Column(Text, nullable=False)  # Jinja2 template
    body_text = Column(Text, nullable=True)   # Plain text version
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<EmailTemplate(name={self.name})>"

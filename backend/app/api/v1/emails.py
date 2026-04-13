"""
Email API endpoints for sending and managing emails.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from typing import Optional, List

from app.core.database import get_db
from app.core.email_service import EmailService, EmailTemplateRenderer
from app.models.email import Email, EmailTemplate
from app.dependencies.auth import require_permission

router = APIRouter(prefix="/emails", tags=["Emails"])

email_service = EmailService()


class SendEmailRequest(BaseModel):
    """Request model for sending a single email."""
    recipient_email: EmailStr
    recipient_name: Optional[str] = None
    subject: str
    body_html: str
    body_text: Optional[str] = None
    email_type: Optional[str] = None


class QueueEmailRequest(BaseModel):
    """Request model for queueing an email for later sending."""
    recipient_email: EmailStr
    recipient_name: Optional[str] = None
    subject: str
    body_html: str
    body_text: Optional[str] = None
    email_type: Optional[str] = None
    send_at: Optional[str] = None  # ISO format datetime (future feature)


class EmailResponse(BaseModel):
    """Response model for email operations."""
    id: str
    recipient_email: str
    subject: str
    status: str
    created_at: str
    sent_at: Optional[str] = None


class EmailTemplateResponse(BaseModel):
    """Response model for email templates."""
    id: str
    name: str
    subject: str
    description: Optional[str] = None


@router.post("/send")
async def send_email(
    request: SendEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("admin:manage_users")),
) -> dict:
    """
    Send an email immediately.
    
    Requires admin permission.
    Email is tracked in database for auditing.
    """
    try:
        success = await email_service.send_email_async(
            recipient_email=request.recipient_email,
            recipient_name=request.recipient_name,
            subject=request.subject,
            body_html=request.body_html,
            body_text=request.body_text,
            db_session=db,
            email_type=request.email_type,
            related_user_id=current_user.id,
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email. Please try again."
            )
        
        return {
            "status": "sent",
            "recipient": request.recipient_email,
            "message": "Email sent successfully"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending email: {str(e)}"
        )


@router.post("/queue")
async def queue_email(
    request: QueueEmailRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("admin:manage_users")),
) -> dict:
    """
    Queue an email for sending (immediately or at scheduled time).
    
    Requires admin permission.
    """
    try:
        # For now, send immediately (future: add scheduled sending)
        background_tasks.add_task(
            email_service.send_email_async,
            request.recipient_email,
            request.subject,
            request.body_html,
            request.body_text,
            request.recipient_name,
            db,
            request.email_type,
            current_user.id,
        )
        
        return {
            "status": "queued",
            "recipient": request.recipient_email,
            "message": "Email queued for sending"
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error queueing email: {str(e)}"
        )


@router.get("/history")
async def get_email_history(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("admin:manage_users")),
) -> dict:
    """
    Get email sending history (admin only).
    
    Returns paginated list of sent emails.
    """
    try:
        # Get total count
        count_result = await db.execute(select(Email))
        total = len(count_result.scalars().all())
        
        # Get paginated results
        result = await db.execute(
            select(Email)
            .order_by(Email.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        emails = result.scalars().all()
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "emails": [
                {
                    "id": email.id,
                    "recipient_email": email.recipient_email,
                    "recipient_name": email.recipient_name,
                    "subject": email.subject,
                    "status": email.status.value,
                    "email_type": email.email_type,
                    "created_at": email.created_at.isoformat(),
                    "sent_at": email.sent_at.isoformat() if email.sent_at else None,
                    "retry_count": email.retry_count,
                }
                for email in emails
            ]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving email history: {str(e)}"
        )


@router.get("/templates")
async def get_email_templates(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("admin:manage_users")),
) -> dict:
    """
    Get all available email templates.
    
    Useful for viewing available template names and subjects.
    """
    try:
        result = await db.execute(select(EmailTemplate))
        templates = result.scalars().all()
        
        return {
            "total": len(templates),
            "templates": [
                {
                    "id": template.id,
                    "name": template.name,
                    "subject": template.subject,
                    "description": template.description,
                }
                for template in templates
            ]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving templates: {str(e)}"
        )


@router.get("/templates/{template_name}")
async def get_email_template(
    template_name: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("admin:manage_users")),
):
    """
    Get a specific email template by name.
    
    Returns full template content for preview or editing.
    """
    try:
        result = await db.execute(
            select(EmailTemplate).where(EmailTemplate.name == template_name)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template '{template_name}' not found"
            )
        
        return {
            "id": template.id,
            "name": template.name,
            "subject": template.subject,
            "body_html": template.body_html,
            "body_text": template.body_text,
            "description": template.description,
            "created_at": template.created_at.isoformat(),
            "updated_at": template.updated_at.isoformat(),
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving template: {str(e)}"
        )


@router.get("/{email_id}")
async def get_email(
    email_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("admin:manage_users")),
):
    """
    Get details of a specific email by ID.
    """
    try:
        result = await db.execute(select(Email).where(Email.id == email_id))
        email = result.scalar_one_or_none()
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found"
            )
        
        return {
            "id": email.id,
            "recipient_email": email.recipient_email,
            "recipient_name": email.recipient_name,
            "subject": email.subject,
            "body_html": email.body_html,
            "body_text": email.body_text,
            "status": email.status.value,
            "email_type": email.email_type,
            "created_at": email.created_at.isoformat(),
            "sent_at": email.sent_at.isoformat() if email.sent_at else None,
            "error_message": email.error_message,
            "retry_count": email.retry_count,
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving email: {str(e)}"
        )

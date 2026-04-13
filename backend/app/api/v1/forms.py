from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, or_
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List
import uuid
import re

from app.core.database import get_db
from app.core import redis_client as rc
from app.core.audit import log_audit_task
from app.models.form import FormLink, FormSubmission
from app.models.student import Student
from app.dependencies.auth import require_permission, get_current_user

router = APIRouter(prefix="/forms", tags=["Forms & Submissions"])

_FORMS_LIST_KEY = "cache:forms:links"

class FormFieldDef(BaseModel):
    name: str # e.g. "first_name"
    label: str # e.g. "First Name"
    required: bool
    type: str # e.g. "text", "email", "date"

class CreateFormLinkRequest(BaseModel):
    title: str
    allowed_fields: List[FormFieldDef]

class ToggleFormStatusRequest(BaseModel):
    is_active: bool

class ApproveSubmissionRequest(BaseModel):
    force_update: bool = False


# ── Form Submission Validation ────────────────────────────────────────────────
class FormSubmissionData(BaseModel):
    """Validated form submission schema with constraints."""
    
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    class_name: Optional[str] = Field(None, max_length=50)
    roll_no: Optional[str] = Field(None, max_length=50)
    admission_no: Optional[str] = Field(None, max_length=50)
    mobile_numbers: Optional[List[str]] = Field(None, max_items=5)
    address: Optional[str] = Field(None, max_length=500)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    zip_code: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[str] = None
    enrollment_date: Optional[str] = None
    
    @validator("date_of_birth", "enrollment_date", pre=True)
    def validate_dates(cls, v):
        """Validate date format (YYYY-MM-DD)."""
        if v is None:
            return v
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', str(v)):
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v
    
    @validator("mobile_numbers", pre=True)
    def validate_mobile_numbers(cls, v):
        """Validate mobile numbers."""
        if v is None:
            return v
        if not isinstance(v, list):
            raise ValueError("mobile_numbers must be a list")
        for num in v:
            if not isinstance(num, str) or len(num) < 7 or len(num) > 20:
                raise ValueError("Invalid phone number format")
        return v
    
    @validator("first_name", "last_name", pre=True)
    def sanitize_names(cls, v):
        """Sanitize names to prevent XSS."""
        if v is None:
            return v
        # Only allow letters, numbers, spaces, hyphens, apostrophes
        if not re.match(r"^[a-zA-Z0-9\s\-']+$", str(v)):
            raise ValueError("Name contains invalid characters")
        return str(v).strip()
    
    class Config:
        extra = "forbid"  # Reject unknown fields

# ── ADMIN: FORM LINKS ─────────────────────────────────────────────────────────

@router.get("/")
async def list_form_links(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("students:read")),
):
    """List all created form links."""
    cached = await rc.get_cached_response(_FORMS_LIST_KEY)
    if cached is not None:
        return cached

    result = await db.execute(select(FormLink).order_by(FormLink.created_at.desc()))
    data = [
        {
            "id": f.id,
            "title": f.title,
            "token": f.token,
            "allowed_fields": f.allowed_fields,
            "is_active": f.is_active,
            "created_at": f.created_at,
        }
        for f in result.scalars().all()
    ]
    await rc.cache_response(_FORMS_LIST_KEY, data, ttl=120)
    return data

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_form_link(
    body: CreateFormLinkRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("students:write")),
):
    """Create a new sharable form link with dynamic fields."""
    token = str(uuid.uuid4())[:12].replace("-", "").upper()
    form = FormLink(
        title=body.title,
        token=token,
        allowed_fields=[f.model_dump() for f in body.allowed_fields],
        created_by=current_user.id
    )
    db.add(form)
    await db.commit()
    
    background_tasks.add_task(rc.invalidate_keys, _FORMS_LIST_KEY)
    background_tasks.add_task(log_audit_task, current_user.id, "CREATE_FORM_LINK", "forms", form.id)
    return {"id": form.id, "token": token, "title": form.title}

@router.patch("/{link_id}/status")
async def toggle_form_status(
    link_id: str,
    body: ToggleFormStatusRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("students:write"))
):
    """Block or unblock a public form link."""
    result = await db.execute(select(FormLink).where(FormLink.id == link_id))
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=404, detail="Form link not found")
        
    form.is_active = body.is_active
    await db.commit()
    
    background_tasks.add_task(rc.invalidate_keys, _FORMS_LIST_KEY)
    background_tasks.add_task(log_audit_task, current_user.id, "TOGGLE_FORM", "forms", link_id)
    return {"message": f"Form is now {'active' if body.is_active else 'blocked'}"}

@router.delete("/{link_id}")
async def delete_form_link(
    link_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("students:delete"))
):
    """Deletes a form link and its pending submissions."""
    result = await db.execute(select(FormLink).where(FormLink.id == link_id))
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=404, detail="Form link not found")
        
    await db.execute(delete(FormLink).where(FormLink.id == link_id))
    await db.commit()
    
    background_tasks.add_task(rc.invalidate_keys, _FORMS_LIST_KEY)
    background_tasks.add_task(log_audit_task, current_user.id, "DELETE_FORM", "forms", link_id)
    return {"message": "Form link deleted"}

# ── ADMIN: SUBMISSIONS & APPROVALS ───────────────────────────────────────────

@router.get("/submissions/all")
async def list_submissions(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("students:read")),
):
    """List all submissions (pending, approved, rejected) across all forms."""
    result = await db.execute(
        select(FormSubmission, FormLink.title)
        .join(FormLink, FormLink.id == FormSubmission.form_link_id)
        .order_by(FormSubmission.created_at.desc())
    )
    
    data = []
    for sub, form_title in result.all():
        data.append({
            "id": sub.id,
            "form_id": sub.form_link_id,
            "form_title": form_title,
            "data": sub.submitted_data,
            "status": sub.status,
            "submitted_at": sub.created_at,
        })
    return data

@router.post("/submissions/{sub_id}/approve")
async def approve_submission(
    sub_id: str,
    body: ApproveSubmissionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("students:write"))
):
    """
    Approve a submission and create/update a Student.
    Uses SELECT FOR UPDATE to prevent race conditions.
    """
    # Lock the submission to prevent concurrent approvals
    result = await db.execute(
        select(FormSubmission).where(FormSubmission.id == sub_id).with_for_update()
    )
    sub = result.scalar_one_or_none()
    
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    if sub.status != "pending":
        raise HTTPException(status_code=400, detail=f"Submission is already {sub.status}")

    s_data = sub.submitted_data
    email = s_data.get("email")
    admission_no = s_data.get("admission_no")
    
    # Conflict Detection with locking!
    conflict_student = None
    if email or admission_no:
        conditions = []
        if email: conditions.append(Student.email == email)
        if admission_no: conditions.append(Student.admission_no == admission_no)
        
        # Lock any matching students to prevent concurrent modifications
        existing_res = await db.execute(
            select(Student).where(or_(*conditions)).limit(1).with_for_update()
        )
        conflict_student = existing_res.scalar_one_or_none()
        
    if conflict_student and not body.force_update:
        # Prompt UI for resolution
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Student already exists with this Email or Admission ID.",
                "conflicting_student_id": conflict_student.id,
                "conflicting_student_name": f"{conflict_student.first_name} {conflict_student.last_name}"
            }
        )

    # Convert submitted string to date, handles optional fields
    from datetime import datetime, timezone
    enrollment = None
    if "enrollment_date" in s_data and s_data["enrollment_date"]:
        try:
            enrollment = datetime.fromisoformat(s_data["enrollment_date"])
        except ValueError:
            enrollment = datetime.now(timezone.utc)
            
    # Write to Student
    if conflict_student and body.force_update:
        # Update existing (already locked above)
        for k, v in s_data.items():
            if hasattr(conflict_student, k) and v is not None:
                setattr(conflict_student, k, v)
        if enrollment:
            conflict_student.enrollment_date = enrollment
    else:
        # Create new student
        new_student = Student(
            first_name=s_data.get("first_name", ""),
            last_name=s_data.get("last_name", ""),
            email=s_data.get("email", ""),
            class_name=s_data.get("class_name"),
            roll_no=s_data.get("roll_no"),
            admission_no=s_data.get("admission_no"),
            mobile_numbers=s_data.get("mobile_numbers", []),
            address=s_data.get("address"),
            city=s_data.get("city"),
            state=s_data.get("state"),
            zip_code=s_data.get("zip_code"),
            date_of_birth=s_data.get("date_of_birth"),
            enrollment_date=enrollment,
            submitted_via_form=True,
            form_submission_code=None
        )
        db.add(new_student)

    # Mark submission as approved
    sub.status = "approved"
    await db.commit()
    
    background_tasks.add_task(rc.invalidate_keys, "cache:students:list")
    background_tasks.add_task(log_audit_task, current_user.id, "APPROVE_SUBMISSION", "forms", sub_id)
    return {"message": "Student approved successfully!"}

@router.post("/submissions/{sub_id}/reject")
async def reject_submission(
    sub_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("students:write"))
):
    """Mark a submission as rejected."""
    result = await db.execute(select(FormSubmission).where(FormSubmission.id == sub_id))
    sub = result.scalar_one_or_none()
    
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    sub.status = "rejected"
    await db.commit()
    background_tasks.add_task(log_audit_task, current_user.id, "REJECT_SUBMISSION", "forms", sub_id)
    return {"message": "Submission rejected"}

# ── PUBLIC: FORMS ─────────────────────────────────────────────────────────────

@router.get("/public/{token}")
async def public_get_form(token: str, db: AsyncSession = Depends(get_db)):
    """Fetch active form fields."""
    result = await db.execute(select(FormLink).where(FormLink.token == token, FormLink.is_active == True))
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=404, detail="Form link is invalid or has been deactivated.")
        
    return {
        "id": form.id,
        "title": form.title,
        "allowed_fields": form.allowed_fields
    }

@router.post("/public/{token}/submit")
async def public_submit_form(
    token: str,
    data: FormSubmissionData,
    db: AsyncSession = Depends(get_db)
):
    """
    Accept public data submission with full validation.
    - Schema validation (types, lengths, formats)
    - Field validation against form configuration
    - XSS/injection protection
    """
    # Get the form link
    result = await db.execute(
        select(FormLink).where(FormLink.token == token, FormLink.is_active == True)
    )
    form = result.scalar_one_or_none()
    if not form:
        raise HTTPException(
            status_code=404,
            detail="Form link is invalid or has been deactivated."
        )
    
    # Validate submitted fields against form's allowed_fields
    allowed_field_names = {field["name"] for field in form.allowed_fields}
    submitted_data = data.dict(exclude_unset=True)
    submitted_field_names = set(submitted_data.keys())
    
    # Check for unexpected fields
    unexpected_fields = submitted_field_names - allowed_field_names
    if unexpected_fields:
        raise HTTPException(
            status_code=400,
            detail=f"Unexpected fields: {', '.join(unexpected_fields)}"
        )
    
    # Check for required fields
    required_fields = {f["name"] for f in form.allowed_fields if f.get("required", False)}
    missing_required = required_fields - submitted_field_names
    if missing_required:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required fields: {', '.join(missing_required)}"
        )
    
    # Create submission with validated data
    sub = FormSubmission(
        form_link_id=form.id,
        submitted_data=submitted_data,
        status="pending"
    )
    db.add(sub)
    await db.commit()
    
    return {
        "message": "Thank you! Your information has been submitted successfully and is pending review.",
        "submission_id": sub.id
    }

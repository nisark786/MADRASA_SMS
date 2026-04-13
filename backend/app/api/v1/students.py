from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import uuid
from datetime import datetime, timezone

from app.core.database import get_db
from app.core import redis_client as rc
from app.core.audit import log_audit_task
from app.models.student import Student
from app.models.user import User
from app.dependencies.auth import require_permission, get_current_user

router = APIRouter(prefix="/students", tags=["Students"])

# Cache key constants
_STUDENTS_LIST_KEY = "cache:students:list"
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 500

# Columns safe to expose
_STUDENT_COLS = (
    Student.id, Student.first_name, Student.last_name,
    Student.email, Student.class_name, Student.roll_no,
    Student.admission_no, Student.mobile_numbers, Student.address,
    Student.city, Student.state, Student.zip_code,
    Student.date_of_birth, Student.enrollment_date,
    Student.is_active, Student.notes, Student.submitted_via_form,
    Student.created_at, Student.updated_at,
)


class CreateStudentRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    class_name: Optional[str] = None
    roll_no: Optional[str] = None
    admission_no: Optional[str] = None
    mobile_numbers: Optional[List[str]] = []
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    date_of_birth: Optional[str] = None
    enrollment_date: Optional[str] = None
    notes: Optional[str] = None


class UpdateStudentRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    class_name: Optional[str] = None
    roll_no: Optional[str] = None
    admission_no: Optional[str] = None
    mobile_numbers: Optional[List[str]] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    date_of_birth: Optional[str] = None
    enrollment_date: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


# ── AUTHENTICATED ENDPOINTS ────────────────────────────────────────────────────

@router.get("/")
async def list_students(
    skip: int = 0,
    limit: int = DEFAULT_PAGE_SIZE,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("students:read")),
):
    """List students with pagination. Cached in Redis, invalidated on any write."""
    # Validate and constrain pagination parameters
    limit = min(max(limit, 1), MAX_PAGE_SIZE)
    skip = max(skip, 0)
    
    # ⚡ Cache hit path (~5ms) with pagination key
    cache_key = f"{_STUDENTS_LIST_KEY}:{skip}:{limit}"
    cached = await rc.get_cached_response(cache_key)
    if cached is not None:
        return cached

    # ❄️ Cache miss: query DB with pagination
    result = await db.execute(
        select(*_STUDENT_COLS)
        .order_by(Student.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = [dict(r) for r in result.mappings().all()]
    
    # Cache with 5-minute TTL for pagination
    await rc.cache_response(cache_key, rows, ttl=300)
    return rows


@router.get("/{student_id}")
async def get_student(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("students:read")),
):
    """Get a single student by ID. Cached for 5 minutes."""
    cache_key = f"cache:student:{student_id}"
    cached = await rc.get_cached_response(cache_key)
    if cached is not None:
        return cached
    
    result = await db.execute(
        select(*_STUDENT_COLS).where(Student.id == student_id)
    )
    student = result.mappings().one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Cache individual student for 5 minutes
    await rc.cache_response(cache_key, dict(student), ttl=300)
    return student


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_student(
    body: CreateStudentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("students:write")),
):
    """Create a new student. Invalidates list cache."""
    student = Student(
        first_name=body.first_name,
        last_name=body.last_name,
        email=body.email,
        class_name=body.class_name,
        roll_no=body.roll_no,
        admission_no=body.admission_no,
        mobile_numbers=body.mobile_numbers,
        address=body.address,
        city=body.city,
        state=body.state,
        zip_code=body.zip_code,
        date_of_birth=body.date_of_birth,
        enrollment_date=datetime.fromisoformat(body.enrollment_date) if body.enrollment_date else datetime.now(timezone.utc),
        notes=body.notes,
        submitted_via_form=False,
    )
    db.add(student)
    
    try:
        await db.flush()
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        if "email" in str(e).lower():
            raise HTTPException(status_code=400, detail="Email already exists")
        raise HTTPException(status_code=400, detail="Duplicate entry or constraint violation")

    # Invalidate cache + log audit in background
    background_tasks.add_task(rc.invalidate_keys, _STUDENTS_LIST_KEY)
    background_tasks.add_task(log_audit_task, current_user.id, "CREATE_STUDENT", "students", student.id)

    return {"id": student.id, "first_name": student.first_name, "last_name": student.last_name, "email": student.email}


@router.patch("/{student_id}")
async def update_student(
    student_id: str,
    body: UpdateStudentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("students:write")),
):
    """Update student details. Invalidates list and individual cache."""
    result = await db.execute(select(Student.id).where(Student.id == student_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Student not found")

    updates: dict = {}
    if body.first_name is not None:   updates["first_name"] = body.first_name
    if body.last_name is not None:    updates["last_name"] = body.last_name
    if body.class_name is not None:   updates["class_name"] = body.class_name
    if body.roll_no is not None:      updates["roll_no"] = body.roll_no
    if body.admission_no is not None: updates["admission_no"] = body.admission_no
    if body.mobile_numbers is not None: updates["mobile_numbers"] = body.mobile_numbers
    if body.address is not None:      updates["address"] = body.address
    if body.city is not None:         updates["city"] = body.city
    if body.state is not None:        updates["state"] = body.state
    if body.zip_code is not None:     updates["zip_code"] = body.zip_code
    if body.date_of_birth is not None: updates["date_of_birth"] = body.date_of_birth
    if body.is_active is not None:    updates["is_active"] = body.is_active
    if body.notes is not None:        updates["notes"] = body.notes
    if body.email is not None:
        updates["email"] = body.email

    if updates:
        try:
            await db.execute(update(Student).where(Student.id == student_id).values(**updates))
            await db.commit()
        except IntegrityError as e:
            await db.rollback()
            if "email" in str(e).lower():
                raise HTTPException(status_code=400, detail="Email already in use")
            raise HTTPException(status_code=400, detail="Constraint violation")

    # Invalidate both list and individual caches
    background_tasks.add_task(rc.invalidate_keys, _STUDENTS_LIST_KEY, f"cache:student:{student_id}")
    background_tasks.add_task(log_audit_task, current_user.id, "UPDATE_STUDENT", "students", student_id)
    return {"message": "Student updated"}


@router.delete("/{student_id}")
async def delete_student(
    student_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("students:delete")),
):
    """Delete a student. Invalidates list cache."""
    result = await db.execute(select(Student.id).where(Student.id == student_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Student not found")

    await db.execute(delete(Student).where(Student.id == student_id))
    await db.commit()

    background_tasks.add_task(rc.invalidate_keys, _STUDENTS_LIST_KEY)
    background_tasks.add_task(log_audit_task, current_user.id, "DELETE_STUDENT", "students", student_id)
    return {"message": "Student deleted"}


# ── PUBLIC ENDPOINTS ──────────────────────────────────────────────────────────

@router.post("/public/submit-form")
async def submit_student_form(
    body: CreateStudentRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Public: submit a student form without authentication."""
    form_code = str(uuid.uuid4())[:8].upper()
    student = Student(
        first_name=body.first_name, last_name=body.last_name, email=body.email,
        class_name=body.class_name, roll_no=body.roll_no, admission_no=body.admission_no,
        mobile_numbers=body.mobile_numbers, address=body.address, city=body.city,
        state=body.state, zip_code=body.zip_code, date_of_birth=body.date_of_birth,
        enrollment_date=datetime.fromisoformat(body.enrollment_date) if body.enrollment_date else datetime.now(timezone.utc),
        notes=body.notes, submitted_via_form=True, form_submission_code=form_code,
    )
    db.add(student)
    
    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        if "email" in str(e).lower():
            raise HTTPException(status_code=400, detail="Email already submitted")
        raise HTTPException(status_code=400, detail="Submission failed due to duplicate entry")

    # Invalidate list cache in background (non-blocking)
    background_tasks.add_task(rc.invalidate_keys, _STUDENTS_LIST_KEY)

    return {"message": "Thank you! Your information has been submitted successfully.", "submission_code": form_code}


@router.get("/public/form-status/{submission_code}")
async def check_form_status(submission_code: str, db: AsyncSession = Depends(get_db)):
    """Public: check submission status by code."""
    result = await db.execute(
        select(Student).where(Student.form_submission_code == submission_code)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Submission not found")

    return {
        "id": student.id,
        "name": f"{student.first_name} {student.last_name}",
        "email": student.email,
        "status": "Received" if student.submitted_via_form else "Updated",
        "submitted_at": student.created_at,
    }

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    class_name: Mapped[str] = mapped_column(String(50), nullable=True)
    roll_no: Mapped[str] = mapped_column(String(50), nullable=True)
    admission_no: Mapped[str] = mapped_column(String(50), nullable=True)
    mobile_numbers: Mapped[list] = mapped_column(JSON, default=list, nullable=True)
    address: Mapped[str] = mapped_column(String(255), nullable=True)
    city: Mapped[str] = mapped_column(String(100), nullable=True)
    state: Mapped[str] = mapped_column(String(100), nullable=True)
    zip_code: Mapped[str] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[str] = mapped_column(String(20), nullable=True)  # ISO 8601 format
    enrollment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    submitted_via_form: Mapped[bool] = mapped_column(Boolean, default=False)  # True if submitted by public form
    form_submission_code: Mapped[str] = mapped_column(String(50), nullable=True, unique=True, index=True)  # Unique code for share links
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

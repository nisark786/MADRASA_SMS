import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean, JSON, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class FormLink(Base):
    __tablename__ = "form_links"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    token: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    allowed_fields: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_by: Mapped[str] = mapped_column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    submissions = relationship("FormSubmission", back_populates="form_link", cascade="all, delete-orphan")


class FormSubmission(Base):
    __tablename__ = "form_submissions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    form_link_id: Mapped[str] = mapped_column(String, ForeignKey("form_links.id", ondelete="CASCADE"), nullable=False, index=True)
    submitted_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True) # pending, approved, rejected
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    form_link = relationship("FormLink", back_populates="submissions")

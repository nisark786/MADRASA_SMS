"""Database backup models for tracking and managing backups."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Boolean, BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DatabaseBackup(Base):
    """
    Tracks database backups created by administrators.
    
    Stores metadata about each backup including:
    - When it was created
    - Who created it
    - Status (pending, completed, failed)
    - Size and location
    - Restore history
    """
    __tablename__ = "database_backups"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Backup metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)  # e.g., "backup_2026-04-13_14-30-45"
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    
    # Backup details
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # pending, in_progress, completed, failed
    file_path: Mapped[str] = mapped_column(String(500), nullable=True)  # Path where backup is stored
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=True)  # Size in bytes
    
    # Backup statistics
    table_count: Mapped[int] = mapped_column(BigInteger, default=0)
    record_count: Mapped[int] = mapped_column(BigInteger, default=0)
    
    # Backup triggers
    is_automated: Mapped[bool] = mapped_column(Boolean, default=False)  # True if created by automated task
    created_by_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=True)
    
    # Backup content
    backup_type: Mapped[str] = mapped_column(String(20), default="full")  # full, incremental
    includes_data: Mapped[bool] = mapped_column(Boolean, default=True)
    includes_schema: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Compression
    is_compressed: Mapped[bool] = mapped_column(Boolean, default=True)
    compression_format: Mapped[str] = mapped_column(String(20), nullable=True)  # gzip, bzip2, etc.
    
    # Encryption
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=False)
    encryption_algorithm: Mapped[str] = mapped_column(String(50), nullable=True)
    
    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Expiration
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Error handling
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])
    restore_jobs: Mapped[list["BackupRestore"]] = relationship(
        "BackupRestore",
        back_populates="backup",
        cascade="all, delete-orphan",
    )

    def is_valid(self) -> bool:
        """Check if backup is still valid (not expired)."""
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return self.status == "completed"

    def duration_seconds(self) -> int:
        """Get backup duration in seconds."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return 0


class BackupRestore(Base):
    """
    Tracks database restore operations performed from backups.
    
    Maintains audit trail of all restore attempts and their outcomes.
    """
    __tablename__ = "backup_restores"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Restore details
    backup_id: Mapped[str] = mapped_column(String, ForeignKey("database_backups.id"), nullable=False, index=True)
    
    # Restore action
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # pending, in_progress, completed, failed, rolled_back
    restore_mode: Mapped[str] = mapped_column(String(20), nullable=False)  # full_restore, point_in_time
    
    # Restore metadata
    started_by_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    target_database: Mapped[str] = mapped_column(String(255), nullable=True)  # If restoring to different DB
    
    # Restore progress
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Restore details
    records_restored: Mapped[int] = mapped_column(BigInteger, default=0)
    tables_restored: Mapped[int] = mapped_column(BigInteger, default=0)
    
    # Error handling
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    
    # Relationships
    backup = relationship("DatabaseBackup", back_populates="restore_jobs")
    started_by = relationship("User", foreign_keys=[started_by_id])

    def duration_seconds(self) -> int:
        """Get restore duration in seconds."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return 0


class BackupSchedule(Base):
    """
    Backup schedule configuration for automated backups.
    
    Allows administrators to configure recurring backup jobs.
    """
    __tablename__ = "backup_schedules"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Schedule configuration
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    
    # Enable/disable
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Frequency
    frequency: Mapped[str] = mapped_column(String(20), nullable=False)  # daily, weekly, monthly
    time_of_day: Mapped[str] = mapped_column(String(5), nullable=False)  # HH:MM format
    day_of_week: Mapped[str] = mapped_column(String(20), nullable=True)  # For weekly: mon, tue, etc.
    day_of_month: Mapped[int] = mapped_column(BigInteger, nullable=True)  # For monthly: 1-31
    
    # Backup configuration
    backup_type: Mapped[str] = mapped_column(String(20), default="full")  # full, incremental
    compression_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    encryption_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Retention policy
    retention_days: Mapped[int] = mapped_column(BigInteger, default=30)  # Keep backups for N days
    max_backups: Mapped[int] = mapped_column(BigInteger, default=10)  # Max number of backups to keep
    
    # Metadata
    created_by_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    last_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    next_run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    created_by = relationship("User", foreign_keys=[created_by_id])

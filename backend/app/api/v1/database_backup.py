"""Database backup and recovery API endpoints."""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.core.database import get_db
from app.core.security import get_current_user, require_admin
from app.core.backup_service import DatabaseBackupService
from app.models.user import User
from app.models.database_backup import DatabaseBackup, BackupRestore, BackupSchedule
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/backups", tags=["backups"])
backup_service = DatabaseBackupService()


# ============================================================================
# Database Backup Endpoints
# ============================================================================

@router.post("/", response_model=dict)
def create_backup(
    description: str = Query(None, max_length=500),
    backup_type: str = Query("full"),
    compress: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """
    Create a new database backup.
    
    - **Requires admin role**
    - Creates a backup using pg_dump
    - Optionally compresses with gzip
    - Returns backup details
    """
    success, message, backup = backup_service.create_backup(
        db=db,
        user=current_user,
        description=description,
        backup_type=backup_type,
        compress=compress,
        is_automated=False,
    )
    
    if not success:
        # Log failed backup attempt
        audit_log = AuditLog(
            action="backup_create_failed",
            resource_type="DatabaseBackup",
            resource_id=backup.id if backup else None,
            user_id=current_user.id,
            details={"error": message, "description": description},
        )
        db.add(audit_log)
        db.commit()
        raise HTTPException(status_code=400, detail=message)
    
    # Log successful backup creation
    audit_log = AuditLog(
        action="backup_created",
        resource_type="DatabaseBackup",
        resource_id=backup.id,
        user_id=current_user.id,
        details={
            "name": backup.name,
            "description": description,
            "backup_type": backup_type,
            "compressed": compress,
        },
    )
    db.add(audit_log)
    db.commit()
    
    return {
        "success": True,
        "message": message,
        "backup": {
            "id": backup.id,
            "name": backup.name,
            "status": backup.status,
            "file_size": backup.file_size,
            "created_at": backup.created_at.isoformat(),
            "completed_at": backup.completed_at.isoformat() if backup.completed_at else None,
        },
    }


@router.get("/", response_model=dict)
def list_backups(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    status: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """
    List all database backups with pagination and filtering.
    
    - **Requires admin role**
    - Supports filtering by status
    - Returns paginated list of backups
    """
    query = select(DatabaseBackup).order_by(desc(DatabaseBackup.created_at))
    
    if status:
        query = query.where(DatabaseBackup.status == status)
    
    # Get total count
    count_result = db.execute(select(DatabaseBackup))
    total = len(count_result.scalars().all())
    
    # Get paginated results
    offset = (page - 1) * page_size
    result = db.execute(query.offset(offset).limit(page_size))
    backups = result.scalars().all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "backups": [
            {
                "id": b.id,
                "name": b.name,
                "description": b.description,
                "status": b.status,
                "file_size": b.file_size,
                "file_size_mb": b.file_size / (1024 * 1024) if b.file_size else None,
                "backup_type": b.backup_type,
                "is_compressed": b.is_compressed,
                "is_automated": b.is_automated,
                "created_by": b.created_by.username if b.created_by else None,
                "created_at": b.created_at.isoformat(),
                "started_at": b.started_at.isoformat() if b.started_at else None,
                "completed_at": b.completed_at.isoformat() if b.completed_at else None,
                "duration_seconds": b.duration_seconds(),
                "is_valid": b.is_valid(),
                "expires_at": b.expires_at.isoformat() if b.expires_at else None,
                "error_message": b.error_message,
            }
            for b in backups
        ],
    }


@router.get("/{backup_id}", response_model=dict)
def get_backup(
    backup_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """
    Get detailed backup information.
    
    - **Requires admin role**
    - Returns full backup details
    """
    result = db.execute(select(DatabaseBackup).where(DatabaseBackup.id == backup_id))
    backup = result.scalar_one_or_none()
    
    if not backup:
        raise HTTPException(status_code=404, detail="Backup not found")
    
    # Get restore history for this backup
    restore_result = db.execute(
        select(BackupRestore).where(BackupRestore.backup_id == backup_id)
    )
    restore_jobs = restore_result.scalars().all()
    
    return {
        "id": backup.id,
        "name": backup.name,
        "description": backup.description,
        "status": backup.status,
        "file_path": backup.file_path,
        "file_size": backup.file_size,
        "file_size_mb": backup.file_size / (1024 * 1024) if backup.file_size else None,
        "backup_type": backup.backup_type,
        "is_compressed": backup.is_compressed,
        "compression_format": backup.compression_format,
        "is_encrypted": backup.is_encrypted,
        "is_automated": backup.is_automated,
        "created_by": backup.created_by.username if backup.created_by else None,
        "created_at": backup.created_at.isoformat(),
        "started_at": backup.started_at.isoformat() if backup.started_at else None,
        "completed_at": backup.completed_at.isoformat() if backup.completed_at else None,
        "duration_seconds": backup.duration_seconds(),
        "is_valid": backup.is_valid(),
        "expires_at": backup.expires_at.isoformat() if backup.expires_at else None,
        "error_message": backup.error_message,
        "restore_history": [
            {
                "id": r.id,
                "status": r.status,
                "restore_mode": r.restore_mode,
                "started_by": r.started_by.username if r.started_by else None,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
                "duration_seconds": r.duration_seconds(),
                "error_message": r.error_message,
            }
            for r in restore_jobs
        ],
    }


@router.post("/{backup_id}/restore", response_model=dict)
def restore_backup(
    backup_id: str,
    restore_mode: str = Query("full_restore"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """
    Restore database from a backup.
    
    - **Requires admin role**
    - Restores database from specified backup
    - Creates restore audit trail
    - WARNING: This will overwrite current database!
    """
    success, message = backup_service.restore_backup(
        db=db,
        backup_id=backup_id,
        user=current_user,
        restore_mode=restore_mode,
    )
    
    if not success:
        # Log failed restore
        audit_log = AuditLog(
            action="backup_restore_failed",
            resource_type="DatabaseBackup",
            resource_id=backup_id,
            user_id=current_user.id,
            details={"error": message, "restore_mode": restore_mode},
        )
        db.add(audit_log)
        db.commit()
        raise HTTPException(status_code=400, detail=message)
    
    # Log successful restore
    audit_log = AuditLog(
        action="backup_restored",
        resource_type="DatabaseBackup",
        resource_id=backup_id,
        user_id=current_user.id,
        details={"restore_mode": restore_mode},
    )
    db.add(audit_log)
    db.commit()
    
    return {"success": True, "message": message}


@router.delete("/{backup_id}", response_model=dict)
def delete_backup(
    backup_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """
    Delete a backup and its files.
    
    - **Requires admin role**
    - Removes backup from database and filesystem
    - Cannot be undone
    """
    success, message = backup_service.delete_backup(db=db, backup_id=backup_id)
    
    if not success:
        audit_log = AuditLog(
            action="backup_delete_failed",
            resource_type="DatabaseBackup",
            resource_id=backup_id,
            user_id=current_user.id,
            details={"error": message},
        )
        db.add(audit_log)
        db.commit()
        raise HTTPException(status_code=400, detail=message)
    
    # Log successful deletion
    audit_log = AuditLog(
        action="backup_deleted",
        resource_type="DatabaseBackup",
        resource_id=backup_id,
        user_id=current_user.id,
        details={},
    )
    db.add(audit_log)
    db.commit()
    
    return {"success": True, "message": message}


@router.get("/stats/summary", response_model=dict)
def get_backup_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """
    Get backup statistics and summary.
    
    - **Requires admin role**
    - Returns backup counts, sizes, and recent backup info
    """
    summary = backup_service.get_backup_summary(db=db)
    return summary


# ============================================================================
# Backup Schedule Endpoints
# ============================================================================

@router.post("/schedules", response_model=dict)
def create_backup_schedule(
    name: str,
    description: str = None,
    frequency: str = "daily",  # daily, weekly, monthly
    time_of_day: str = "02:00",  # HH:MM format
    day_of_week: str = None,  # For weekly: mon, tue, etc.
    day_of_month: int = None,  # For monthly: 1-31
    backup_type: str = "full",
    compression_enabled: bool = True,
    encryption_enabled: bool = False,
    retention_days: int = 30,
    max_backups: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """
    Create a new backup schedule for automated backups.
    
    - **Requires admin role**
    - Configures recurring backup jobs
    - Supports daily, weekly, monthly frequencies
    """
    # Validate frequency
    if frequency not in ["daily", "weekly", "monthly"]:
        raise HTTPException(status_code=400, detail="Invalid frequency")
    
    # Create schedule
    schedule = BackupSchedule(
        name=name,
        description=description,
        frequency=frequency,
        time_of_day=time_of_day,
        day_of_week=day_of_week,
        day_of_month=day_of_month,
        backup_type=backup_type,
        compression_enabled=compression_enabled,
        encryption_enabled=encryption_enabled,
        retention_days=retention_days,
        max_backups=max_backups,
        created_by_id=current_user.id,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    
    # Log schedule creation
    audit_log = AuditLog(
        action="backup_schedule_created",
        resource_type="BackupSchedule",
        resource_id=schedule.id,
        user_id=current_user.id,
        details={
            "name": name,
            "frequency": frequency,
            "time_of_day": time_of_day,
            "retention_days": retention_days,
        },
    )
    db.add(audit_log)
    db.commit()
    
    return {
        "success": True,
        "message": f"Backup schedule created: {name}",
        "schedule": {
            "id": schedule.id,
            "name": schedule.name,
            "description": schedule.description,
            "frequency": schedule.frequency,
            "time_of_day": schedule.time_of_day,
            "is_enabled": schedule.is_enabled,
        },
    }


@router.get("/schedules", response_model=dict)
def list_backup_schedules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """
    List all backup schedules.
    
    - **Requires admin role**
    - Returns paginated list of backup schedules
    """
    query = select(BackupSchedule).order_by(desc(BackupSchedule.created_at))
    
    # Get total count
    count_result = db.execute(select(BackupSchedule))
    total = len(count_result.scalars().all())
    
    # Get paginated results
    offset = (page - 1) * page_size
    result = db.execute(query.offset(offset).limit(page_size))
    schedules = result.scalars().all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
        "schedules": [
            {
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "frequency": s.frequency,
                "time_of_day": s.time_of_day,
                "day_of_week": s.day_of_week,
                "day_of_month": s.day_of_month,
                "is_enabled": s.is_enabled,
                "backup_type": s.backup_type,
                "compression_enabled": s.compression_enabled,
                "retention_days": s.retention_days,
                "max_backups": s.max_backups,
                "created_by": s.created_by.username if s.created_by else None,
                "created_at": s.created_at.isoformat(),
                "last_run_at": s.last_run_at.isoformat() if s.last_run_at else None,
                "next_run_at": s.next_run_at.isoformat() if s.next_run_at else None,
            }
            for s in schedules
        ],
    }


@router.patch("/schedules/{schedule_id}", response_model=dict)
def update_backup_schedule(
    schedule_id: str,
    is_enabled: bool = None,
    frequency: str = None,
    time_of_day: str = None,
    retention_days: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """
    Update a backup schedule.
    
    - **Requires admin role**
    - Modify schedule settings
    """
    result = db.execute(select(BackupSchedule).where(BackupSchedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Update fields if provided
    if is_enabled is not None:
        schedule.is_enabled = is_enabled
    if frequency:
        schedule.frequency = frequency
    if time_of_day:
        schedule.time_of_day = time_of_day
    if retention_days:
        schedule.retention_days = retention_days
    
    db.commit()
    db.refresh(schedule)
    
    # Log schedule update
    audit_log = AuditLog(
        action="backup_schedule_updated",
        resource_type="BackupSchedule",
        resource_id=schedule.id,
        user_id=current_user.id,
        details={
            "frequency": frequency,
            "time_of_day": time_of_day,
            "is_enabled": is_enabled,
        },
    )
    db.add(audit_log)
    db.commit()
    
    return {
        "success": True,
        "message": f"Schedule updated: {schedule.name}",
        "schedule": {
            "id": schedule.id,
            "name": schedule.name,
            "frequency": schedule.frequency,
            "time_of_day": schedule.time_of_day,
            "is_enabled": schedule.is_enabled,
        },
    }


@router.delete("/schedules/{schedule_id}", response_model=dict)
def delete_backup_schedule(
    schedule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """
    Delete a backup schedule.
    
    - **Requires admin role**
    - Remove automated backup schedule
    """
    result = db.execute(select(BackupSchedule).where(BackupSchedule.id == schedule_id))
    schedule = result.scalar_one_or_none()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    schedule_name = schedule.name
    db.delete(schedule)
    db.commit()
    
    # Log schedule deletion
    audit_log = AuditLog(
        action="backup_schedule_deleted",
        resource_type="BackupSchedule",
        resource_id=schedule_id,
        user_id=current_user.id,
        details={"name": schedule_name},
    )
    db.add(audit_log)
    db.commit()
    
    return {"success": True, "message": f"Schedule deleted: {schedule_name}"}

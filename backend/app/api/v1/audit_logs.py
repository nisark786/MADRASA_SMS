"""Audit logs endpoints for viewing and exporting audit records."""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select, and_
import csv
import json
from io import StringIO

from app.api.deps import get_db
from app.dependencies.auth import require_permission, get_current_user
from app.models.audit_log import AuditLog
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/audit-logs", tags=["Audit Logs"])


class AuditLogResponse(BaseModel):
    """Response model for audit log entries."""
    id: int
    user_id: str
    action: str
    resource: str
    resource_id: str
    details: dict
    ip_address: str
    created_at: str
    
    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Response model for audit log list."""
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[AuditLogResponse]


@router.get("/", response_model=AuditLogListResponse)
async def list_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    action: str = Query(None),
    resource: str = Query(None),
    user_id: str = Query(None),
    start_date: str = Query(None),  # ISO format: 2026-04-13
    end_date: str = Query(None),    # ISO format: 2026-04-13
    db: Session = Depends(get_db),
    _=Depends(require_permission("admin:view_audit")),
):
    """
    List audit logs with optional filtering.
    
    Query parameters:
    - page: Page number (1-indexed)
    - page_size: Results per page (1-500)
    - action: Filter by action (e.g., "CREATE_USER", "LOGIN")
    - resource: Filter by resource (e.g., "users", "roles")
    - user_id: Filter by user who performed action
    - start_date: Filter by start date (ISO format)
    - end_date: Filter by end date (ISO format)
    
    Returns:
        Paginated audit log entries with metadata
    """
    try:
        # Build query
        query = select(AuditLog)
        
        # Apply filters
        filters = []
        
        if action:
            filters.append(AuditLog.action == action)
        
        if resource:
            filters.append(AuditLog.resource == resource)
        
        if user_id:
            filters.append(AuditLog.user_id == user_id)
        
        if start_date:
            try:
                start = datetime.fromisoformat(start_date).replace(tzinfo=None)
                filters.append(AuditLog.created_at >= start)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use ISO format (YYYY-MM-DD)"
                )
        
        if end_date:
            try:
                end = datetime.fromisoformat(end_date).replace(tzinfo=None)
                end = end.replace(hour=23, minute=59, second=59)
                filters.append(AuditLog.created_at <= end)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use ISO format (YYYY-MM-DD)"
                )
        
        if filters:
            query = query.where(and_(*filters))
        
        # Get total count
        count_query = select(AuditLog.__table__.c)
        if filters:
            count_query = count_query.where(and_(*filters))
        
        result = await db.execute(
            select(AuditLog).where(and_(*filters)) if filters else select(AuditLog)
        )
        total = len(result.all())
        
        # Calculate pagination
        total_pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size
        
        # Fetch paginated results
        result = await db.execute(
            query.order_by(AuditLog.created_at.desc()).limit(page_size).offset(offset)
        )
        logs = result.scalars().all()
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "items": [
                {
                    "id": log.id,
                    "user_id": log.user_id,
                    "action": log.action,
                    "resource": log.resource,
                    "resource_id": log.resource_id,
                    "details": log.details or {},
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat() if log.created_at else None,
                }
                for log in logs
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing audit logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        )


@router.get("/{log_id}")
async def get_audit_log(
    log_id: int,
    db: Session = Depends(get_db),
    _=Depends(require_permission("admin:view_audit")),
):
    """
    Get a specific audit log entry.
    
    Args:
        log_id: ID of the audit log entry
    
    Returns:
        dict: Detailed audit log entry
    """
    try:
        result = await db.execute(
            select(AuditLog).where(AuditLog.id == log_id)
        )
        log = result.scalar_one_or_none()
        
        if not log:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit log entry not found"
            )
        
        # Get user info if available
        user = None
        if log.user_id:
            result = await db.execute(
                select(User).where(User.id == log.user_id)
            )
            user = result.scalar_one_or_none()
        
        return {
            "id": log.id,
            "user_id": log.user_id,
            "user": {
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            } if user else None,
            "action": log.action,
            "resource": log.resource,
            "resource_id": log.resource_id,
            "details": log.details or {},
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting audit log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit log"
        )


@router.get("/export/csv")
async def export_audit_logs_csv(
    action: str = Query(None),
    resource: str = Query(None),
    user_id: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None),
    db: Session = Depends(get_db),
    _=Depends(require_permission("admin:view_audit")),
):
    """
    Export audit logs as CSV.
    
    Returns:
        CSV file with audit log data
    """
    try:
        # Build query
        query = select(AuditLog)
        filters = []
        
        if action:
            filters.append(AuditLog.action == action)
        
        if resource:
            filters.append(AuditLog.resource == resource)
        
        if user_id:
            filters.append(AuditLog.user_id == user_id)
        
        if start_date:
            try:
                start = datetime.fromisoformat(start_date).replace(tzinfo=None)
                filters.append(AuditLog.created_at >= start)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format"
                )
        
        if end_date:
            try:
                end = datetime.fromisoformat(end_date).replace(tzinfo=None)
                end = end.replace(hour=23, minute=59, second=59)
                filters.append(AuditLog.created_at <= end)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format"
                )
        
        if filters:
            query = query.where(and_(*filters))
        
        # Fetch all results
        result = await db.execute(
            query.order_by(AuditLog.created_at.desc())
        )
        logs = result.scalars().all()
        
        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "ID",
            "Timestamp",
            "User ID",
            "Action",
            "Resource",
            "Resource ID",
            "Details",
            "IP Address",
        ])
        
        # Write data
        for log in logs:
            writer.writerow([
                log.id,
                log.created_at.isoformat() if log.created_at else "",
                log.user_id or "",
                log.action,
                log.resource or "",
                log.resource_id or "",
                json.dumps(log.details) if log.details else "",
                log.ip_address or "",
            ])
        
        return {
            "success": True,
            "csv_data": output.getvalue(),
            "filename": f"audit_logs_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting audit logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export audit logs"
        )


@router.get("/stats/summary")
async def get_audit_log_summary(
    days: int = Query(7, ge=1, le=365),
    db: Session = Depends(get_db),
    _=Depends(require_permission("admin:view_audit")),
):
    """
    Get summary statistics of audit logs.
    
    Args:
        days: Number of days to look back (1-365)
    
    Returns:
        dict: Summary statistics
    """
    try:
        start_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        result = await db.execute(
            select(AuditLog).where(AuditLog.created_at >= start_date)
        )
        logs = result.scalars().all()
        
        # Calculate statistics
        actions = {}
        resources = {}
        
        for log in logs:
            actions[log.action] = actions.get(log.action, 0) + 1
            resources[log.resource] = resources.get(log.resource, 0) + 1
        
        return {
            "total_events": len(logs),
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": datetime.now(timezone.utc).isoformat(),
            "actions": actions,
            "resources": resources,
            "events_per_day": len(logs) / max(days, 1),
        }
    
    except Exception as e:
        logger.error(f"Error getting audit log summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit log summary"
        )

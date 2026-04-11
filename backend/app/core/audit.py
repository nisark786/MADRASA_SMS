from app.core.database import AsyncSessionLocal
from app.models.audit_log import AuditLog


async def log_audit_task(user_id: str, action: str, resource: str, resource_id: str):
    """Background task: records audit logs without blocking the main request."""
    async with AsyncSessionLocal() as db:
        db.add(AuditLog(
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
        ))
        await db.commit()

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core import redis_client as rc
from app.models.user import User
from app.models.permission import Permission
from app.dependencies.auth import require_permission

router = APIRouter(prefix="/permissions", tags=["Permissions"])

_PERMISSIONS_LIST_KEY = "cache:permissions:list"


@router.get("/")
async def list_permissions(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("admin:manage_roles")),
):
    """
    Permissions are static data — cached for 1 hour.
    Almost always a Redis hit (~2ms).
    """
    cached = await rc.get_cached_response(_PERMISSIONS_LIST_KEY)
    if cached is not None:
        return cached

    result = await db.execute(select(Permission).order_by(Permission.module, Permission.action))
    data = [
        {"id": p.id, "name": p.name, "module": p.module, "action": p.action, "description": p.description}
        for p in result.scalars().all()
    ]
    await rc.cache_response(_PERMISSIONS_LIST_KEY, data, ttl=3600)
    return data

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert
from pydantic import BaseModel
from typing import Optional
from collections import defaultdict
import asyncio

from app.core.database import get_db
from app.core import redis_client as rc
from app.core.audit import log_audit_task
from app.models.user import User
from app.models.role import Role, UserRole
from app.models.permission import Permission, RolePermission
from app.dependencies.auth import require_permission

router = APIRouter(prefix="/roles", tags=["Roles"])

_ROLES_LIST_KEY = "cache:roles:list"


class CreateRoleRequest(BaseModel):
    name: str
    description: Optional[str] = None
    permission_ids: list[str] = []


class UpdateRoleRequest(BaseModel):
    description: Optional[str] = None
    permission_ids: Optional[list[str]] = None
    is_active: Optional[bool] = None


@router.get("/")
async def list_roles(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("admin:manage_roles")),
):
    """List all roles with permissions. Cached in Redis."""
    cached = await rc.get_cached_response(_ROLES_LIST_KEY)
    if cached is not None:
        return cached

    roles_result = await db.execute(select(Role).order_by(Role.created_at.desc()))
    roles = roles_result.scalars().all()
    if not roles:
        return []

    role_ids = [r.id for r in roles]
    perms_result = await db.execute(
        select(RolePermission.role_id, Permission.id, Permission.name)
        .join(Permission, Permission.id == RolePermission.permission_id)
        .where(RolePermission.role_id.in_(role_ids))
    )
    role_perms: dict[str, list] = defaultdict(list)
    for role_id, perm_id, perm_name in perms_result.all():
        role_perms[role_id].append({"id": perm_id, "name": perm_name})

    data = [
        {
            "id":             r.id,
            "name":           r.name,
            "description":    r.description,
            "is_system_role": r.is_system_role,
            "is_active":      r.is_active,
            "permissions":    role_perms.get(r.id, []),
        }
        for r in roles
    ]
    await rc.cache_response(_ROLES_LIST_KEY, data, ttl=300)
    return data


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_role(
    body: CreateRoleRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("admin:manage_roles")),
):
    existing = await db.execute(select(Role.id).where(Role.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Role name already exists")

    role = Role(name=body.name, description=body.description, created_by=current_user.id)
    db.add(role)
    await db.flush()

    if body.permission_ids:
        await db.execute(
            insert(RolePermission),
            [{"role_id": role.id, "permission_id": pid, "granted_by": current_user.id} for pid in body.permission_ids],
        )

    await db.commit()
    background_tasks.add_task(rc.invalidate_keys, _ROLES_LIST_KEY)
    background_tasks.add_task(log_audit_task, current_user.id, "CREATE_ROLE", "roles", role.id)
    return {"id": role.id, "name": role.name}


@router.patch("/{role_id}")
async def update_role(
    role_id: str,
    body: UpdateRoleRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("admin:manage_roles")),
):
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    if body.description is not None: role.description = body.description
    if body.is_active is not None:   role.is_active = body.is_active

    if body.permission_ids is not None:
        await db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
        if body.permission_ids:
            await db.execute(
                insert(RolePermission),
                [{"role_id": role_id, "permission_id": pid, "granted_by": current_user.id} for pid in body.permission_ids],
            )

        # Invalidate ALL users with this role (permissions changed)
        ur_result = await db.execute(
            select(UserRole.user_id).where(UserRole.role_id == role_id)
        )
        user_ids = [row[0] for row in ur_result.all()]
        await asyncio.gather(
            *[rc.invalidate_user_permissions(uid) for uid in user_ids],
            *[rc.invalidate_user_object(uid) for uid in user_ids],
        )
        # Also invalidate per-user widget caches (permission-gated)
        background_tasks.add_task(rc.invalidate_pattern, "cache:widgets:*")

    await db.commit()
    background_tasks.add_task(rc.invalidate_keys, _ROLES_LIST_KEY)
    background_tasks.add_task(log_audit_task, current_user.id, "UPDATE_ROLE", "roles", role_id)
    return {"message": "Role updated"}


@router.delete("/{role_id}")
async def delete_role(
    role_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("admin:manage_roles")),
):
    result = await db.execute(select(Role.id, Role.is_system_role).where(Role.id == role_id))
    role = result.one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    if role.is_system_role:
        raise HTTPException(status_code=400, detail="System roles cannot be deleted")

    await db.execute(delete(Role).where(Role.id == role_id))
    await db.commit()
    background_tasks.add_task(rc.invalidate_keys, _ROLES_LIST_KEY)
    return {"message": "Role deleted"}

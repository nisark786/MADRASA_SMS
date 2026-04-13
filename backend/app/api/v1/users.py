from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, insert, update
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
import asyncio

from app.core.database import get_db
from app.core.security import hash_password
from app.core import redis_client as rc
from app.core.audit import log_audit_task
from app.core.password_policy import PasswordPolicy, PasswordChangeRequest
from app.models.user import User
from app.models.role import UserRole
from app.dependencies.auth import require_permission, get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

_USERS_LIST_KEY = "cache:users:list"

_USER_COLS = (
    User.id, User.username, User.email,
    User.first_name, User.last_name,
    User.is_active, User.last_login, User.created_at,
)


class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role_ids: list[str] = []
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """Validate password against policy."""
        is_valid, error_msg = PasswordPolicy.validate(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v


class UpdateUserRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: Optional[bool] = None
    role_ids: Optional[list[str]] = None


@router.get("/")
async def list_users(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_permission("admin:manage_users")),
):
    """List all users. Cached in Redis, invalidated on any write."""
    cached = await rc.get_cached_response(_USERS_LIST_KEY)
    if cached is not None:
        return cached

    result = await db.execute(select(*_USER_COLS).order_by(User.created_at.desc()))
    rows = [dict(r) for r in result.mappings().all()]
    await rc.cache_response(_USERS_LIST_KEY, rows, ttl=120)
    return rows


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    body: CreateUserRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("admin:manage_users")),
):
    existing = await db.execute(
        select(User.id).where(
            (User.email == body.email) | (User.username == body.username)
        ).limit(1)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email or username already exists")

    user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        first_name=body.first_name,
        last_name=body.last_name,
        created_by=current_user.id,
    )
    db.add(user)
    await db.flush()

    if body.role_ids:
        await db.execute(
            insert(UserRole),
            [{"user_id": user.id, "role_id": rid, "assigned_by": current_user.id} for rid in body.role_ids],
        )

    await db.commit()

    background_tasks.add_task(rc.invalidate_keys, _USERS_LIST_KEY)
    background_tasks.add_task(log_audit_task, current_user.id, "CREATE_USER", "users", user.id)
    return {"id": user.id, "username": user.username, "email": user.email}


@router.patch("/{user_id}")
async def update_user(
    user_id: str,
    body: UpdateUserRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("admin:manage_users")),
):
    result = await db.execute(select(User.id).where(User.id == user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")

    updates: dict = {}
    if body.first_name is not None: updates["first_name"] = body.first_name
    if body.last_name is not None:  updates["last_name"] = body.last_name
    if body.is_active is not None:  updates["is_active"] = body.is_active

    if updates:
        await db.execute(update(User).where(User.id == user_id).values(**updates))

    if body.role_ids is not None:
        await db.execute(delete(UserRole).where(UserRole.user_id == user_id))
        if body.role_ids:
            await db.execute(
                insert(UserRole),
                [{"user_id": user_id, "role_id": rid, "assigned_by": current_user.id} for rid in body.role_ids],
            )
        # Invalidate permission + user object caches for this user
        await asyncio.gather(
            rc.invalidate_user_permissions(user_id),
            rc.invalidate_user_object(user_id),
        )

    await db.commit()

    background_tasks.add_task(rc.invalidate_keys, _USERS_LIST_KEY)
    background_tasks.add_task(log_audit_task, current_user.id, "UPDATE_USER", "users", user_id)
    return {"message": "User updated"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("admin:manage_users")),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    result = await db.execute(select(User.id).where(User.id == user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")

    await asyncio.gather(
        db.execute(delete(User).where(User.id == user_id)),
        rc.invalidate_user_permissions(user_id),
        rc.invalidate_user_object(user_id),
    )
    await db.commit()

    background_tasks.add_task(rc.invalidate_keys, _USERS_LIST_KEY)
    background_tasks.add_task(log_audit_task, current_user.id, "DELETE_USER", "users", user_id)
    return {"message": "User deleted"}


@router.post("/change-password")
async def change_password(
    body: PasswordChangeRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change password for the current user.
    
    Requires:
    - Current password verification
    - New password matching confirmation password
    - New password passing security policy (12+ chars, uppercase, lowercase, digit, special char)
    """
    from app.core.security import verify_password
    
    # Fetch user from DB to get password hash
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    
    # Verify current password
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect")
    
    # Check that new password is different from current
    if verify_password(body.new_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New password must be different from current password")
    
    # Update password (validation already done by Pydantic model)
    new_hash = hash_password(body.new_password)
    await db.execute(
        update(User).where(User.id == current_user.id).values(password_hash=new_hash)
    )
    await db.commit()
    
    # Invalidate user cache to force re-login
    await rc.invalidate_user_object(current_user.id)
    
    # Log audit event
    background_tasks.add_task(log_audit_task, current_user.id, "CHANGE_PASSWORD", "users", current_user.id)
    
    return {"message": "Password changed successfully"}

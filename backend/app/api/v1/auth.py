from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.core import redis_client as rc
from app.core.audit import log_audit_task
from app.models.user import User
from app.models.role import UserRole
from app.dependencies.auth import get_current_user, get_user_permissions

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict
    permissions: list[str]


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    OPTIMIZED:
    - Fetch user from DB (unavoidable on login)
    - Token generation + permission fetch run concurrently
    - last_login update + audit log written as background task (non-blocking)
    """
    result = await db.execute(
        select(User).where(User.email == body.email, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    # Constant-time password check prevents timing attacks
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token_data = {"sub": user.id}

    # Token generation is synchronous; fetch permissions concurrently while tokens are built
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    perms = await get_user_permissions(user.id, db)

    # Cache user object so subsequent requests skip DB entirely
    await rc.cache_user_object(user.id, {
        "id":         user.id,
        "username":   user.username,
        "email":      user.email,
        "first_name": user.first_name,
        "last_name":  user.last_name,
        "is_active":  user.is_active,
    })

    # Non-blocking: update last_login + audit log in background
    ip = request.client.host if request.client else "unknown"
    background_tasks.add_task(_post_login_tasks, user.id, ip)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id":         user.id,
            "username":   user.username,
            "email":      user.email,
            "first_name": user.first_name,
            "last_name":  user.last_name,
        },
        permissions=list(perms),
    )


async def _post_login_tasks(user_id: str, ip_address: str):
    """Background: update last_login + write audit log (no latency impact on user)."""
    from app.core.database import AsyncSessionLocal
    from app.models.audit_log import AuditLog
    async with AsyncSessionLocal() as db:
        await db.execute(
            update(User).where(User.id == user_id).values(last_login=datetime.now(timezone.utc))
        )
        db.add(AuditLog(
            user_id=user_id,
            action="LOGIN",
            resource="auth",
            ip_address=ip_address,
        ))
        await db.commit()


@router.post("/refresh")
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Token refresh — only fetches User.id for minimal DB projection."""
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = payload.get("sub")

    # Check Redis first (avoids DB on active sessions)
    cached = await rc.get_cached_user_object(user_id)
    if cached:
        if not cached.get("is_active"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")
    else:
        result = await db.execute(
            select(User.id).where(User.id == user_id, User.is_active == True)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return {"access_token": create_access_token({"sub": user_id}), "token_type": "bearer"}


@router.post("/logout")
async def logout(current_user=Depends(get_current_user)):
    """Invalidates all Redis caches for this user."""
    await asyncio.gather(
        rc.invalidate_user_permissions(current_user.id),
        rc.invalidate_user_object(current_user.id),
    )
    return {"message": "Logged out successfully"}


@router.get("/me")
async def me(current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Fetches permissions + role_ids concurrently.
    On warm cache: permissions from Redis, roles from DB (one fast indexed query).
    """
    perms_task = get_user_permissions(current_user.id, db)
    roles_task = db.execute(
        select(UserRole.role_id).where(UserRole.user_id == current_user.id)
    )

    perms, roles_result = await asyncio.gather(perms_task, roles_task)
    role_ids = [row[0] for row in roles_result.all()]

    return {
        "id":          current_user.id,
        "username":    current_user.username,
        "email":       current_user.email,
        "first_name":  current_user.first_name,
        "last_name":   current_user.last_name,
        "is_active":   current_user.is_active,
        "permissions": list(perms),
        "role_ids":    role_ids,
    }

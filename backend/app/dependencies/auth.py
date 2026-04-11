from types import SimpleNamespace
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, distinct

from app.core.database import get_db
from app.core.security import decode_token
from app.core import redis_client as rc
from app.models.user import User
from app.models.role import UserRole
from app.models.permission import RolePermission, Permission

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    ZERO-DB AUTH on warm path:
    1. JWT decode      (~0.1ms  — pure Python)
    2. Redis obj cache (~1ms    — single GET)
    3. DB fetch        (only on cold start / cache miss)

    Returns either the real ORM User (cold path) or a lightweight SimpleNamespace
    proxy (warm path) with the same fields used by route handlers.
    """
    token = credentials.credentials
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")

    # ⚡ Warm path: full user object in Redis (zero DB)
    cached = await rc.get_cached_user_object(user_id)
    if cached is not None:
        if not cached.get("is_active"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")
        # Return a lightweight proxy that acts like an ORM User for route handlers
        return SimpleNamespace(**cached)

    # ❄️ Cold path: hit DB, populate cache
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Cache minimal user object for future requests
    await rc.cache_user_object(user_id, {
        "id":         user.id,
        "username":   user.username,
        "email":      user.email,
        "first_name": user.first_name,
        "last_name":  user.last_name,
        "is_active":  user.is_active,
    })
    return user


async def get_user_permissions(user_id: str, db: AsyncSession) -> set[str]:
    """
    Permission resolution:
    1. Pipeline EXISTS + SMEMBERS in ONE Redis round-trip (hot path)
    2. On cache miss: single 3-table JOIN query (cold path)
    3. Write back to cache for future requests
    """
    # Hot path: single pipeline call (fixed double round-trip bug)
    cached = await rc.get_cached_permissions(user_id)
    if cached is not None:
        return cached

    # Cold path: DB JOIN
    result = await db.execute(
        select(distinct(Permission.name))
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .where(UserRole.user_id == user_id)
    )
    perms = {row[0] for row in result.all()}

    await rc.cache_user_permissions(user_id, list(perms))
    return perms


def require_permission(permission: str):
    """
    Permission check dependency factory.
    Hot path: JWT decode (~0.1ms) + Redis pipeline (~1ms) + Python set O(1)
    Total overhead: ~2ms
    """
    async def checker(
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        perms = await get_user_permissions(current_user.id, db)
        if permission not in perms:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: '{permission}' required",
            )
        return current_user
    return checker


def require_any_permission(*permissions: str):
    """Passes if user has at least one of the given permissions."""
    perm_set = frozenset(permissions)

    async def checker(
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        perms = await get_user_permissions(current_user.id, db)
        if not perms.intersection(perm_set):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Permission denied",
            )
        return current_user
    return checker

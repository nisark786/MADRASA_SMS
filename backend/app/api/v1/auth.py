import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.core import redis_client as rc
from app.core.rate_limit import RateLimiter
from app.core.csrf import CSRFProtection
from app.core.config import settings
from app.core.audit import log_audit_task
from app.core.cache_helpers import cache_user_after_create, invalidate_user_caches
from app.models.user import User
from app.models.role import UserRole
from app.dependencies.auth import get_current_user, get_user_permissions

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
    permissions: list[str]
    csrf_token: str


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login")
async def login(
    body: LoginRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    SECURE LOGIN with:
    - httpOnly cookies for tokens (XSS protection)
    - CSRF tokens (CSRF protection)
    - Rate limiting with response headers (brute force protection)
    - Background task for audit log
    """
    from datetime import datetime, timezone
    
    # Get client IP for rate limiting and logging
    ip = request.client.host if request.client else "unknown"
    
    # Apply rate limiting per email (attempts from same email)
    limiter = RateLimiter(rc.redis_client)
    limit = settings.LOGIN_RATE_LIMIT
    email_rate_info = await limiter.check_rate_limit(
        identifier=f"login:email:{body.email}",
        limit=limit,
        window_seconds=60,  # 60 second window
        action="login"
    )
    
    # Apply rate limiting per IP (attempts from same IP)
    ip_rate_info = await limiter.check_rate_limit(
        identifier=f"login:ip:{ip}",
        limit=limit * 2,  # More lenient per IP (accounts for multiple users)
        window_seconds=60,
        action="login"
    )
    
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
    await cache_user_after_create(user.id, {
        "id":         user.id,
        "username":   user.username,
        "email":      user.email,
        "first_name": user.first_name,
        "last_name":  user.last_name,
        "is_active":  user.is_active,
    })

    # Non-blocking: update last_login + audit log in background
    background_tasks.add_task(_post_login_tasks, user.id, ip)
    
    # Create response with httpOnly cookies for tokens
    response = JSONResponse({
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id":         user.id,
            "username":   user.username,
            "email":      user.email,
            "first_name": user.first_name,
            "last_name":  user.last_name,
        },
        "permissions": list(perms),
    })
    
    # Set access token as httpOnly secure cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  # Only sent over HTTPS in production
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    
    # Set refresh token as httpOnly secure cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )
    
    # Set CSRF token cookie
    csrf = CSRFProtection(rc.redis_client)
    csrf_token = await csrf.set_csrf_cookie(response, user.id)
    
    # Include CSRF token in response body (needed for frontend to send in headers)
    response.body = response.body.replace(
        b'"permissions"',
        b'"csrf_token":"' + csrf_token.encode() + b'","permissions"'
    )
    
    # Add rate limit headers for client-side rate limit handling
    reset_time = int(datetime.now(timezone.utc).timestamp()) + email_rate_info["reset_in_seconds"]
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(email_rate_info["remaining"])
    response.headers["X-RateLimit-Reset"] = str(reset_time)
    response.headers["X-RateLimit-Reset-After"] = str(email_rate_info["reset_in_seconds"])
    
    return response



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
async def refresh(request: Request):
    """
    Token refresh using httpOnly cookies.
    Returns new access token as httpOnly cookie and CSRF token in response body.
    """
    # Get refresh token from httpOnly cookie
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token found")
    
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = payload.get("sub")

    # Check Redis first (avoids DB on active sessions)
    cached = await rc.get_cached_user_object(user_id)
    if cached:
        if not cached.get("is_active"):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")
    else:
        # If not cached, verify user still exists (rare case)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User session expired")

    # Generate new access token
    new_access_token = create_access_token({"sub": user_id})
    
    # Create response with new access token cookie
    response = JSONResponse({
        "token_type": "bearer",
    })
    
    # Set new access token as httpOnly cookie
    response.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    
    # Generate and set new CSRF token
    csrf = CSRFProtection(rc.redis_client)
    csrf_token = await csrf.set_csrf_cookie(response, user_id)
    
    # Add CSRF token to response body
    response.body = response.body.replace(
        b'"token_type"',
        b'"csrf_token":"' + csrf_token.encode() + b'","token_type"'
    )
    
    return response


@router.post("/logout")
async def logout(current_user=Depends(get_current_user)):
    """
    Logout: Invalidates session and clears cookies.
    Clears access token, refresh token, and CSRF token cookies.
    """
    # Invalidate caches
    await invalidate_user_caches(current_user.id)
    
    # Create response and clear cookies
    response = JSONResponse({"message": "Logged out successfully"})
    
    # Clear token cookies
    response.delete_cookie("access_token", samesite="strict")
    response.delete_cookie("refresh_token", samesite="strict")
    response.delete_cookie("csrf_token", samesite="strict")
    
    return response


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

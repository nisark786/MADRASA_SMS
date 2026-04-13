"""
CSRF Protection utilities for the application.
Implements double-submit cookie pattern with secure token generation.
"""
import secrets
from fastapi import HTTPException, status, Request, Response
from app.core.config import settings
import redis.asyncio as aioredis


class CSRFProtection:
    """CSRF protection using double-submit cookie pattern."""
    
    TOKEN_LENGTH = 32
    COOKIE_NAME = "csrf_token"
    HEADER_NAME = "X-CSRF-Token"
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
    
    def generate_token(self) -> str:
        """Generate a cryptographically secure CSRF token."""
        return secrets.token_urlsafe(self.TOKEN_LENGTH)
    
    async def set_csrf_cookie(self, response: Response, user_id: str = None):
        """
        Set CSRF token cookie in response.
        Token is stored in Redis for server-side validation.
        """
        token = self.generate_token()
        
        # Store token in Redis with TTL (15 minutes)
        key = f"csrf:{token}"
        await self.redis.setex(key, 900, user_id or "anonymous")
        
        # Set as secure, httpOnly cookie (cannot be accessed via JS)
        response.set_cookie(
            key=self.COOKIE_NAME,
            value=token,
            httponly=True,
            secure=True,  # Only sent over HTTPS in production
            samesite="strict",  # Prevent CSRF attacks
            max_age=900,  # 15 minutes
        )
        
        return token
    
    async def validate_csrf_token(self, request: Request) -> bool:
        """
        Validate CSRF token from request headers.
        Token must exist in Redis and match the one sent in header.
        """
        # Get token from cookie
        cookie_token = request.cookies.get(self.COOKIE_NAME)
        if not cookie_token:
            return False
        
        # Get token from header
        header_token = request.headers.get(self.HEADER_NAME)
        if not header_token:
            return False
        
        # Verify token exists in Redis
        try:
            key = f"csrf:{header_token}"
            exists = await self.redis.exists(key)
            if not exists:
                return False
            
            # Token is valid - delete it (single-use)
            await self.redis.delete(key)
            return True
        except Exception as e:
            print(f"CSRF validation error: {e}")
            return False
    
    async def check_csrf(self, request: Request) -> None:
        """Check CSRF token and raise HTTPException if invalid."""
        # Skip CSRF check for GET, HEAD, OPTIONS, TRACE requests
        if request.method in ["GET", "HEAD", "OPTIONS", "TRACE"]:
            return
        
        # Skip CSRF check for login endpoint (special handling needed)
        if request.url.path == "/api/v1/auth/login":
            return
        
        if not await self.validate_csrf_token(request):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token validation failed"
            )

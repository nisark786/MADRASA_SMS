"""
Rate limiting utilities using Redis for distributed rate limiting.
Implements token bucket algorithm for flexible rate limit configurations.
"""
from datetime import datetime
import redis.asyncio as aioredis
from fastapi import HTTPException, status


class RateLimiter:
    """Token bucket rate limiter using Redis."""
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
    
    async def is_allowed(
        self,
        identifier: str,
        limit: int,
        window_seconds: int,
        action: str = "request"
    ) -> bool:
        """
        Check if a request is allowed under rate limit.
        
        Args:
            identifier: Unique identifier (e.g., IP, user_id, email)
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
            action: Action name for logging
            
        Returns:
            True if allowed, False if rate limited
        """
        key = f"ratelimit:{action}:{identifier}"
        
        try:
            current = await self.redis.incr(key)
            
            if current == 1:
                # First request in this window - set expiry
                await self.redis.expire(key, window_seconds)
            
            if current > limit:
                return False
                
            return True
        except Exception as e:
            # If Redis fails, allow the request (fail-open)
            # but log the error
            print(f"Rate limiter error: {e}")
            return True
    
    async def check_rate_limit(
        self,
        identifier: str,
        limit: int,
        window_seconds: int,
        action: str = "request"
    ) -> dict:
        """
        Check rate limit and raise HTTPException if exceeded.
        Returns rate limit information for use in response headers.
        
        Args:
            identifier: Unique identifier
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
            action: Action name for logging
            
        Returns:
            dict: Rate limit info {limit, remaining, reset_after}
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        remaining_info = await self.get_remaining(identifier, limit, window_seconds, action)
        
        if remaining_info["remaining"] < 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many {action} attempts. Please try again later.",
                headers={
                    "Retry-After": str(remaining_info["reset_in_seconds"]),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(datetime.utcnow().timestamp()) + remaining_info["reset_in_seconds"]),
                }
            )
        
        return remaining_info
    
    async def get_remaining(
        self,
        identifier: str,
        limit: int,
        window_seconds: int,
        action: str = "request"
    ) -> dict:
        """Get current usage and remaining quota."""
        key = f"ratelimit:{action}:{identifier}"
        
        try:
            current = await self.redis.get(key)
            current = int(current) if current else 0
            ttl = await self.redis.ttl(key)
            
            return {
                "limit": limit,
                "current": current,
                "remaining": max(0, limit - current),
                "reset_in_seconds": max(0, ttl) if ttl >= 0 else window_seconds
            }
        except Exception:
            return {
                "limit": limit,
                "current": 0,
                "remaining": limit,
                "reset_in_seconds": window_seconds
            }


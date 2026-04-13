"""
Consolidated cache and helper utilities for user and permission caching.
Reduces code duplication across endpoints.
"""
from app.core import redis_client as rc


async def cache_user_after_create(user_id: str, user_data: dict) -> None:
    """
    Cache a user object after creation/retrieval.
    
    Args:
        user_id: The user's ID
        user_data: Dictionary with user fields (id, username, email, first_name, last_name, is_active)
    """
    await rc.cache_user_object(user_id, user_data)


async def invalidate_user_caches(user_id: str) -> None:
    """
    Invalidate all user-related caches (permissions and user object).
    
    Args:
        user_id: The user's ID
    """
    await rc.invalidate_user_permissions(user_id)
    await rc.invalidate_user_object(user_id)


async def invalidate_multiple_user_caches(user_ids: list[str]) -> None:
    """
    Invalidate caches for multiple users (used in background tasks).
    
    Args:
        user_ids: List of user IDs
    """
    import asyncio
    await asyncio.gather(
        *[rc.invalidate_user_permissions(uid) for uid in user_ids],
        *[rc.invalidate_user_object(uid) for uid in user_ids],
    )

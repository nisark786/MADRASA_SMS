import json
import redis.asyncio as aioredis
from app.core.config import settings

redis_client: aioredis.Redis = None


async def get_redis() -> aioredis.Redis:
    return redis_client


async def init_redis():
    global redis_client
    redis_client = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.aclose()


# ── Constants ─────────────────────────────────────────────────────────────────

PERMS_TTL       = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60  # match token lifetime
USER_CACHE_TTL  = 900    # 15 min — user object
RESPONSE_TTL    = 60     # 60 s  — list endpoint responses
LONG_TTL        = 3600   # 1 hr  — static data (permissions)


# ── Permission cache ──────────────────────────────────────────────────────────

async def cache_user_permissions(user_id: str, permissions: list[str]):
    key = f"perms:{user_id}"
    pipe = redis_client.pipeline()
    pipe.delete(key)  # clear stale set before re-populating
    if permissions:
        pipe.sadd(key, *permissions)
    pipe.expire(key, PERMS_TTL)
    await pipe.execute()


async def get_cached_permissions(user_id: str) -> set[str] | None:
    """Single Redis call — returns None on miss, set on hit (including empty set)."""
    key = f"perms:{user_id}"
    # Use EXISTS + SMEMBERS in a pipeline (2 cmds, 1 round-trip)
    pipe = redis_client.pipeline()
    pipe.exists(key)
    pipe.smembers(key)
    exists, members = await pipe.execute()
    if not exists:
        return None
    return members  # may be empty set — that is valid (user has no permissions)


async def invalidate_user_permissions(user_id: str):
    await redis_client.delete(f"perms:{user_id}")


# ── User object cache (eliminates DB hit on every request) ───────────────────

async def cache_user_object(user_id: str, user_data: dict):
    """Cache minimal user profile (id, username, email, first_name, last_name, is_active)."""
    key = f"user:obj:{user_id}"
    await redis_client.set(key, json.dumps(user_data), ex=USER_CACHE_TTL)


async def get_cached_user_object(user_id: str) -> dict | None:
    """Returns user dict if cached, None on miss."""
    key = f"user:obj:{user_id}"
    val = await redis_client.get(key)
    if val is None:
        return None
    return json.loads(val)


async def invalidate_user_object(user_id: str):
    await redis_client.delete(f"user:obj:{user_id}")


# ── Response-level cache (entire JSON responses) ──────────────────────────────

async def cache_response(key: str, data, ttl: int = RESPONSE_TTL):
    """Serialize and cache a response. data can be list or dict."""
    await redis_client.set(key, json.dumps(data, default=str), ex=ttl)


async def get_cached_response(key: str):
    """Returns deserialized response or None on cache miss."""
    val = await redis_client.get(key)
    if val is None:
        return None
    return json.loads(val)


async def invalidate_keys(*keys: str):
    """Delete one or more exact cache keys."""
    if keys:
        await redis_client.delete(*keys)


async def invalidate_pattern(pattern: str):
    """Delete all keys matching a glob pattern. Use sparingly on large datasets."""
    keys = await redis_client.keys(pattern)
    if keys:
        await redis_client.delete(*keys)

import os
import json
import redis.asyncio as redis
from typing import Any, Optional
from sqlalchemy.orm import Session
from datetime import timedelta

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Create a global Redis connection pool
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def get_cached(key: str) -> Optional[Any]:
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
    except Exception as e:
        print(f"Redis get error: {e}")
    return None

async def set_cached(key: str, value: Any, ttl_seconds: int = 86400) -> bool:
    try:
        serialized = json.dumps(value)
        await redis_client.setex(key, timedelta(seconds=ttl_seconds), serialized)
        return True
    except Exception as e:
        print(f"Redis set error: {e}")
        return False

async def invalidate_pattern(pattern: str) -> int:
    """
    Delete all keys matching a glob pattern, e.g. 'nearby:*'.
    Uses SCAN (non-blocking, cursor-based) instead of KEYS, which would
    block the whole Redis instance on a large keyspace.
    """
    deleted = 0
    try:
        async for key in redis_client.scan_iter(match=pattern, count=100):
            await redis_client.delete(key)
            deleted += 1
    except Exception as e:
        print(f"Redis invalidate error: {e}")
    return deleted
import os
import json
import redis.asyncio as redis
from typing import Any, Optional
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

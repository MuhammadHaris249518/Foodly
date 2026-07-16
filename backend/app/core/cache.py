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

# ─────────────────────────────────────────────────────────────────
# Semantic cache design (Sprint 12 foundation) — NOT wired into /chat.
#
# Intended flow, full wiring deferred to Sprint 12:
#   1. On an incoming /chat message, embed it with embed_query_async().
#   2. Call find_similar_cached_query(db, embedding) — pgvector cosine
#      distance (`<=>`) against chat_query_cache, closest match first.
#   3. If the closest match's distance < SEMANTIC_CACHE_THRESHOLD,
#      treat it as a hit: fetch the full response body from Redis via
#      the matched row's redis_key and return it directly, skipping
#      the LLM call.
#   4. On a miss: run the normal agent as today, then insert the new
#      query's embedding into chat_query_cache and store the response
#      in Redis under a fresh key, so future similar queries hit.
#
# Why this isn't wired into /chat yet: /chat streams a multi-turn
# agent trace (thinking/tool_call/tool_result/token events) rather
# than one JSON blob, so "replay a cached response" needs a decision
# on what gets cached (final answer text only vs. the full event
# stream) and how staleness is bounded for time-sensitive answers
# (e.g. live prices). That's Sprint 12 scope. This sprint only proves
# out the similarity-lookup mechanism below, with a unit test.
# ─────────────────────────────────────────────────────────────────

SEMANTIC_CACHE_THRESHOLD = 0.1


async def find_similar_cached_query(
    db: Session, query_embedding: list, threshold: float = SEMANTIC_CACHE_THRESHOLD
):
    """
    Return the closest previously-cached chat query if its cosine
    distance to query_embedding is below `threshold`, else None.
    Skeleton only — not called from the /chat endpoint yet.
    """
    from ..models.chat_cache import ChatQueryCache  # local import: keep cache.py decoupled from models at load time

    closest = (
        db.query(ChatQueryCache)
        .order_by(ChatQueryCache.embedding.op("<=>")(query_embedding))
        .limit(1)
        .first()
    )
    if closest is None:
        return None

    distance = (
        db.query(ChatQueryCache.embedding.op("<=>")(query_embedding))
        .filter(ChatQueryCache.id == closest.id)
        .scalar()
    )
    if distance is not None and distance < threshold:
        return closest
    return None
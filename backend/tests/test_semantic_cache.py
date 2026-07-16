"""
Unit tests for find_similar_cached_query() — Task 4.4 (Sprint 11 / Day 4).

Strategy
--------
find_similar_cached_query() does a local import of ChatQueryCache inside the
function body (to avoid a circular import at module load time).  That import
chain pulls in models → database → config → pydantic-settings, which requires
DATABASE_URL and SECRET_KEY env vars.

We break that chain by patching ``app.models.chat_cache.ChatQueryCache`` with
a plain MagicMock *before* the function is called, so no real DB/env setup is
needed.  The mock db.query() chain is built to return controlled rows and
distances, letting us verify the threshold logic in pure Python.
"""

import math
import sys
import types
import pytest
from unittest.mock import MagicMock, patch

# ── Minimal stubs so top-level imports in cache.py succeed ────────────────────

# pgvector stub (imported at module level in cache.py)
pgvector_stub = types.ModuleType("pgvector")
pgvector_sql_stub = types.ModuleType("pgvector.sqlalchemy")


class _VectorStub:
    def __init__(self, dim):
        self.dim = dim


pgvector_sql_stub.Vector = _VectorStub
pgvector_stub.sqlalchemy = pgvector_sql_stub
sys.modules.setdefault("pgvector", pgvector_stub)
sys.modules.setdefault("pgvector.sqlalchemy", pgvector_sql_stub)

# redis stub (redis.asyncio used at module level in cache.py)
redis_stub = types.ModuleType("redis")
redis_asyncio_stub = types.ModuleType("redis.asyncio")
redis_asyncio_stub.from_url = MagicMock(return_value=MagicMock())
redis_stub.asyncio = redis_asyncio_stub
sys.modules.setdefault("redis", redis_stub)
sys.modules.setdefault("redis.asyncio", redis_asyncio_stub)

# Now we can safely import the function under test
from app.core.cache import find_similar_cached_query, SEMANTIC_CACHE_THRESHOLD  # noqa: E402


# ── Shared test vectors ────────────────────────────────────────────────────────

QUERY_VEC = [1.0, 0.0, 0.0, 0.0]
NEAR_VEC  = [1.0, 0.0, 0.0, 0.0]   # cosine distance ≈ 0.0 → HIT
FAR_VEC   = [0.0, 1.0, 0.0, 0.0]   # cosine distance ≈ 1.0 → MISS


def _cosine_distance(a: list, b: list) -> float:
    """Pure-Python cosine distance (mirrors pgvector's <=> semantics)."""
    dot   = sum(x * y for x, y in zip(a, b))
    na    = math.sqrt(sum(x * x for x in a))
    nb    = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 1.0
    return 1.0 - dot / (na * nb)


# ── Mock ChatQueryCache that never touches the real DB/settings ────────────────

MockChatQueryCache = MagicMock()


def _make_mock_db(row, distance: float):
    """
    Build a mock db.query(…) chain:
      - First  call → .order_by(…).limit(1).first() → row
      - Second call → .filter(…).scalar()            → distance
    """
    db = MagicMock()

    first_q = MagicMock()
    first_q.order_by.return_value.limit.return_value.first.return_value = row

    scalar_q = MagicMock()
    scalar_q.filter.return_value.scalar.return_value = distance

    db.query.side_effect = [first_q, scalar_q]
    return db


# ── Tests ─────────────────────────────────────────────────────────────────────

PATCH_TARGET = "app.models.chat_cache.ChatQueryCache"


class TestFindSimilarCachedQuery:
    """
    DoD (Task 4.4): a working find_similar_cached_query() helper with a unit
    test that exercises the threshold logic without requiring Postgres/Redis.
    """

    # ── 4.4-a: Identical vector → distance ≈ 0.0 < threshold → HIT ──────────

    @pytest.mark.asyncio
    async def test_returns_row_when_distance_below_threshold(self):
        """Identical embedding → cosine distance ≈ 0.0 → should return the row."""
        cached_row = MagicMock()
        cached_row.id = 1
        cached_row.query_text = "cheap biryani near F-7"
        cached_row.redis_key = "chat:abc123"

        distance = _cosine_distance(QUERY_VEC, NEAR_VEC)   # ≈ 0.0
        assert distance < SEMANTIC_CACHE_THRESHOLD

        db = _make_mock_db(cached_row, distance)

        with patch("app.core.cache.ChatQueryCache", MockChatQueryCache, create=True):
            # Patch the local import inside the function
            with patch.dict(sys.modules, {"app.models.chat_cache": MagicMock(ChatQueryCache=MockChatQueryCache)}):
                result = await find_similar_cached_query(db, QUERY_VEC)

        assert result is cached_row

    # ── 4.4-b: Orthogonal vector → distance ≈ 1.0 ≥ threshold → MISS ────────

    @pytest.mark.asyncio
    async def test_returns_none_when_distance_above_threshold(self):
        """Orthogonal embedding → cosine distance ≈ 1.0 → should return None."""
        cached_row = MagicMock()
        cached_row.id = 2
        cached_row.query_text = "something completely different"
        cached_row.redis_key = "chat:xyz789"

        distance = _cosine_distance(QUERY_VEC, FAR_VEC)    # ≈ 1.0
        assert distance >= SEMANTIC_CACHE_THRESHOLD

        db = _make_mock_db(cached_row, distance)

        with patch.dict(sys.modules, {"app.models.chat_cache": MagicMock(ChatQueryCache=MockChatQueryCache)}):
            result = await find_similar_cached_query(db, QUERY_VEC)

        assert result is None

    # ── 4.4-c: Empty cache → first() returns None → MISS ─────────────────────

    @pytest.mark.asyncio
    async def test_returns_none_when_cache_is_empty(self):
        """When no rows exist in the cache the helper must return None silently."""
        db = MagicMock()
        q = MagicMock()
        q.order_by.return_value.limit.return_value.first.return_value = None
        db.query.return_value = q

        with patch.dict(sys.modules, {"app.models.chat_cache": MagicMock(ChatQueryCache=MockChatQueryCache)}):
            result = await find_similar_cached_query(db, QUERY_VEC)

        assert result is None

    # ── 4.4-d: Custom threshold of 0.0 → even identical vectors miss ─────────

    @pytest.mark.asyncio
    async def test_custom_threshold_respected(self):
        """
        threshold=0.0 means distance must be strictly < 0.0 to hit — impossible.
        Even an identical embedding should return None.
        """
        cached_row = MagicMock()
        cached_row.id = 3

        distance = _cosine_distance(QUERY_VEC, NEAR_VEC)   # ≈ 0.0

        db = _make_mock_db(cached_row, distance)

        with patch.dict(sys.modules, {"app.models.chat_cache": MagicMock(ChatQueryCache=MockChatQueryCache)}):
            result = await find_similar_cached_query(db, QUERY_VEC, threshold=0.0)

        assert result is None

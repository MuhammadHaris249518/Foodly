import os
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

# CHANGED: previously this file independently read DATABASE_URL with its
# own hardcoded fallback:
#   DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/foodly")
# That duplicated (and could silently diverge from) the main app's DB
# config, and carried its own insecure default credential. Now imports the
# single validated settings.DATABASE_URL — one source of truth, and if it's
# missing/insecure, app startup already failed in core/config.py before
# this module is ever reached.
from app.core.config import settings

from urllib.parse import urlsplit, urlunsplit
import structlog

logger = structlog.get_logger(__name__)

DB_URL = settings.DATABASE_URL
if DB_URL.startswith("postgresql+psycopg2://"):
    DB_URL = DB_URL.replace("postgresql+psycopg2://", "postgresql://")

def _mask_db_url(url: str) -> str:
    parts = urlsplit(url)
    if parts.password:
        netloc = parts.netloc.replace(f":{parts.password}@", ":[HIDDEN]@")
    else:
        netloc = parts.netloc
    return urlunsplit((parts.scheme, netloc, parts.path, "", ""))

logger.info("checkpointer_initialized", db_url=_mask_db_url(DB_URL))

_pool = None

@asynccontextmanager
async def get_checkpointer():
    global _pool
    if _pool is None:
        _pool = AsyncConnectionPool(
            conninfo=DB_URL,
            max_size=20,
            kwargs={"autocommit": True}
        )
    saver = AsyncPostgresSaver(_pool)
    await saver.setup()
    yield saver
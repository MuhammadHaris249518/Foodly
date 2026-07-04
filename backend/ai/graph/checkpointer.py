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
from backend.app.core.config import settings

DB_URL = settings.DATABASE_URL
if DB_URL.startswith("postgresql+psycopg2://"):
    DB_URL = DB_URL.replace("postgresql+psycopg2://", "postgresql://")

print(f"DB_URL in checkpointer: {DB_URL.replace('Vu7tDoAbjrPv5OXq', '[HIDDEN]')}")
pool = AsyncConnectionPool(
    conninfo=DB_URL,
    max_size=20,
    kwargs={"autocommit": True}
)

@asynccontextmanager
async def get_checkpointer():
    saver = AsyncPostgresSaver(pool)
    await saver.setup()
    yield saver
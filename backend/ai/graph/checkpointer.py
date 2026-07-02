import os
from contextlib import asynccontextmanager
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/foodly")
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

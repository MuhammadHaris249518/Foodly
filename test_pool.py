import asyncio
from psycopg_pool import AsyncConnectionPool
async def test():
    pool = AsyncConnectionPool(conninfo='postgresql://postgres:pass@localhost:5432/db')
    print('success')
asyncio.run(test())

import asyncio
from psycopg_pool import AsyncConnectionPool
async def test():
    p = AsyncConnectionPool('postgresql://postgres:pass@localhost:5432/db', kwargs={'autocommit': True, 'prepare_threshold': None})
    print('OK')
asyncio.run(test())

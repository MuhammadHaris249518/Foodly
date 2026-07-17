import httpx
import asyncio
async def main():
    async with httpx.AsyncClient() as client:
        async with client.stream('GET', 'http://127.0.0.1:8000/api/v1/agent/live-price?query=biryani') as resp:
            async for chunk in resp.aiter_text():
                print('CHUNK:', chunk)
asyncio.run(main())

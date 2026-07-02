import os
import asyncio
from tavily import TavilyClient

def scrape_web(query: str) -> str:
    """
    Search the web for real-time prices using Tavily Search API or a fallback.
    """
    api_key = os.getenv("TAVILY_API_KEY")

    if not api_key:
        print("Warning: TAVILY_API_KEY not found. Returning mock data.")
        return f"Mock search result: I found {query} on Foodpanda for Rs. 450."

    client = TavilyClient(api_key=api_key)

    try:
        response = client.search(query=query, search_depth="basic", max_results=3)
        results = response.get("results", [])

        context = ""
        for item in results:
            context += f"Source: {item['title']} ({item['url']})\nSnippet: {item['content']}\n\n"

        return context
    except Exception as e:
        return f"Search failed: {str(e)}"


async def scrape_web_async(query: str) -> str:
    """Async wrapper — runs the blocking Tavily call in a thread so it doesn't block the event loop."""
    return await asyncio.to_thread(scrape_web, query)

"""
Refine Query Chain - Uses Groq to improve search queries when initial results have low confidence.
Part of Day 9: Fix Existing AI Code + LangGraph State Design
"""
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
import os

# Groq LLM for fast query refinement
_refine_llm = None

def get_refine_llm():
    """Lazy-load Groq LLM for query refinement."""
    global _refine_llm
    if _refine_llm is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        _refine_llm = ChatGroq(
            api_key=api_key,
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=100  # Keep it short - just a search query
        )
    return _refine_llm


REFINE_QUERY_PROMPT = PromptTemplate(
    input_variables=["original", "results", "meal_context"],
    template="""You are a search query optimization expert for finding food prices in Islamabad, Pakistan.

The original search query: "{original}"
Search results we got (low quality or no price found):
{results}

Meal we're looking for: {meal_context}

Task: Generate a better, more specific search query that will help find the current price of this meal in Islamabad.

Guidelines:
- Include restaurant names if mentioned in results
- Add "2024" or "2025" for recent prices
- Be specific: include area names (F-7, G-9, Blue Area, etc.)
- Keep it under 10 words
- Focus on price keywords: "price", "menu", "cost", "PKR"

Return ONLY the improved search query, nothing else:"""
)


async def refine_search_query(
    original_query: str,
    search_results: str,
    meal_context: str = ""
) -> str:
    """
    Use Groq to refine a search query when initial results are poor.
    
    Args:
        original_query: The initial search query that returned low-quality results
        search_results: The actual results that were returned
        meal_context: Additional context about the meal being searched
    
    Returns:
        A refined search query string
    """
    try:
        llm = get_refine_llm()
        prompt = REFINE_QUERY_PROMPT.format(
            original=original_query,
            results=search_results[:500],  # Limit context length
            meal_context=meal_context
        )
        
        # Use ainvoke for async
        response = await llm.ainvoke(prompt)
        refined = response.content.strip()
        
        # Clean up the response - remove quotes if present
        refined = refined.strip('"').strip("'")
        
        # Ensure it's not too long
        if len(refined) > 100:
            refined = refined[:100]
        
        return refined if refined else original_query
        
    except Exception as e:
        print(f"Query refinement failed: {e}")
        # Fallback: append "price" to original query
        return f"{original_query} price Islamabad"


# Synchronous wrapper for LangGraph nodes (they expect sync functions)
def refine_query_sync(state: dict) -> dict:
    """
    Synchronous wrapper for LangGraph node.
    Refines the search query based on previous results.
    """
    original = state.get("search_query", "")
    results = state.get("search_results", "")
    meal_id = state.get("meal_id")
    
    # Get meal context if available
    meal_context = f"Meal ID: {meal_id}" if meal_id else ""
    
    # Run async function in event loop
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        refined = loop.run_until_complete(
            refine_search_query(original, results, meal_context)
        )
    except RuntimeError:
        # If we're already in an async context
        refined = original
    
    return {
        "search_query": refined,
        "search_results": "",
        "extracted_data": None,
        "retry_reason": f"Low confidence results, refined query to: {refined}"
    }
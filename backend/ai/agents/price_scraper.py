"""
LangGraph Price Scraper Agent - Production Implementation
Day 9: Fix Existing AI Code + LangGraph State Design

Workflow: search → extract → [retry | store | end]
- search: Tavily web search for meal prices
- extract: Groq LLM extracts structured price data
- retry: Refine query and search again (if confidence < 50 and iterations < 3)
- store: Save to pending_verifications table (if confidence >= 50)
- end: Give up after 3 iterations
"""
import os
import asyncio
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from backend.ai.graph.state import AgentState, ExtractedPrice
from backend.ai.tools.search_tools import scrape_web_async
from backend.app.core.database import SessionLocal
from backend.app.models.pending_verification import PendingVerification
from backend.app.models.meal import Meal


def get_groq_llm():
    """Get Groq LLM instance for fast inference."""
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="llama-3.3-70b-versatile",
        temperature=0.2,
        max_tokens=500
    )


# --- Node 1: Search the web ---
async def search_node(state: AgentState) -> Dict[str, Any]:
    """Search the web for meal prices using Tavily."""
    query = state.get("search_query", "")
    meal_id = state.get("meal_id")
    
    # Enhance query with meal context if available
    if meal_id:
        try:
            db = SessionLocal()
            meal = db.query(Meal).filter(Meal.id == meal_id).first()
            if meal:
                query = f"{meal.name} {meal.location or 'Islamabad'} price menu PKR"
            db.close()
        except Exception:
            pass  # Continue with original query if DB lookup fails
    
    print(f"-> Searching web for: {query}")
    results = await scrape_web_async(query)
    
    return {
        "search_results": results,
        "iterations": state.get("iterations", 0) + 1
    }


# --- Node 2: Extract structured data ---
def extract_node(state: AgentState) -> Dict[str, Any]:
    """Extract price information from search results using Groq."""
    print("-> Extracting price using Groq")
    
    search_results = state.get("search_results", "")
    meal_id = state.get("meal_id")
    
    # Get meal context for better extraction
    meal_context = ""
    if meal_id:
        try:
            db = SessionLocal()
            meal = db.query(Meal).filter(Meal.id == meal_id).first()
            if meal:
                meal_context = f"\nMeal we're looking for: {meal.name} at {meal.location or 'Islamabad'}"
            db.close()
        except Exception:
            pass
    
    prompt = f"""You are a food price extraction AI based in Islamabad, Pakistan.
Review the following search results and extract the restaurant name, meal name, and price in PKR.
If multiple prices exist, pick the most recent or most official looking one.

{meal_context}

Search Results:
{search_results}

Instructions:
- Extract the exact price in PKR (Pakistani Rupees)
- If you see multiple prices, choose the most reliable source
- Confidence should be 0-100 based on how clear the price is
- If no price found, set price_pkr to 0 and confidence to 0
"""
    
    llm = get_groq_llm()
    structured_llm = llm.with_structured_output(ExtractedPrice)
    result = structured_llm.invoke(prompt)
    
    return {"extracted_data": result}


# --- Node 3: Retry with refined query ---
def retry_node(state: AgentState) -> Dict[str, Any]:
    """Refine the search query and prepare for retry."""
    print("-> Retrying with refined query")
    
    search_results = state.get("search_results", "")
    original_query = state.get("search_query", "")
    meal_id = state.get("meal_id")
    
    # Get meal context
    meal_context = ""
    if meal_id:
        try:
            db = SessionLocal()
            meal = db.query(Meal).filter(Meal.id == meal_id).first()
            if meal:
                meal_context = f"{meal.name} in {meal.location or 'Islamabad'}"
            db.close()
        except Exception:
            pass
    
    # Use LLM to generate better query
    llm = get_groq_llm()
    prompt = f"""The previous query "{original_query}" returned low-confidence results.

Results we got:
{search_results[:500]}

Meal we're looking for: {meal_context}

Generate a better, more specific search query to find the price.
Guidelines:
- Include restaurant names if mentioned
- Add "2024" or "2025" for recent prices
- Be specific: include area names (F-7, G-9, Blue Area, etc.)
- Focus on price keywords: "price", "menu", "cost", "PKR"
- Keep it under 10 words

Return ONLY the improved search query:"""
    
    try:
        response = llm.invoke(prompt)
        refined_query = response.content.strip().strip('"').strip("'")
        
        # Ensure it's not too long
        if len(refined_query) > 100:
            refined_query = refined_query[:100]
    except Exception as e:
        print(f"Query refinement failed: {e}")
        # Fallback: append "price" to original query
        refined_query = f"{original_query} price Islamabad"
    
    return {
        "search_query": refined_query,
        "search_results": "",
        "extracted_data": None,
        "retry_reason": f"Low confidence results, refined query to: {refined_query}"
    }


# --- Node 4: Store in Database ---
def store_node(state: AgentState) -> Dict[str, Any]:
    """Store extracted price in pending_verifications table."""
    print("-> Storing extracted price in database")
    
    data = state.get("extracted_data")
    if not data or not data.price_pkr or data.price_pkr <= 0:
        print("-> No valid price data to store")
        return state
    
    meal_id = state.get("meal_id")
    thread_id = state.get("thread_id")
    
    if not meal_id:
        print("-> No meal_id provided, cannot store")
        return state
    
    db = SessionLocal()
    try:
        # Check if there's already a pending verification for this meal
        existing = db.query(PendingVerification).filter(
            PendingVerification.meal_id == meal_id,
            PendingVerification.status == "pending"
        ).first()
        
        if existing:
            print(f"-> Meal {meal_id} already has pending verification, skipping")
            return state
        
        # Create new verification
        new_verification = PendingVerification(
            meal_id=meal_id,
            source="web_agent",
            raw_data=data.model_dump(),
            extracted_price=data.price_pkr,
            confidence=data.confidence,
            status="pending",
            agent_thread_id=thread_id
        )
        db.add(new_verification)
        db.commit()
        
        print(f"-> Stored verification: Meal {meal_id}, Price {data.price_pkr} PKR, Confidence {data.confidence}%")
        
    except Exception as e:
        print(f"-> Failed to store verification: {e}")
        db.rollback()
    finally:
        db.close()
    
    return state


# --- Node 5: Human Review (for HITL - Day 13) ---
def human_review_node(state: AgentState) -> Dict[str, Any]:
    """Pause for human review - will be used with interrupt() on Day 13."""
    print("-> Pausing for human review...")
    # This node will be enhanced with LangGraph interrupt() on Day 13
    return state


# --- Conditional Edge (Router) ---
def should_continue(state: AgentState) -> str:
    """
    Decide next action based on extraction results.
    
    Returns:
        "store" - confidence >= 50, store in DB
        "retry" - confidence < 50 and iterations < 3, try again
        "end" - iterations >= 3, give up
    """
    data = state.get("extracted_data")
    iterations = state.get("iterations", 0)
    
    # Success: valid price with good confidence
    if data and data.price_pkr > 0 and data.confidence >= 50:
        print(f"-> Success! Price: {data.price_pkr} PKR, Confidence: {data.confidence}%")
        return "store"
    
    # Failure: exhausted retries
    if iterations >= 3:
        print(f"-> Giving up after {iterations} iterations")
        return "end"
    
    # Retry: low confidence, try again
    print(f"-> Low confidence ({data.confidence if data else 0}%), retrying...")
    return "retry"


# --- Build the Graph ---
def build_price_agent(checkpointer=None):
    """
    Build the LangGraph price scraper agent.
    
    Args:
        checkpointer: Optional LangGraph checkpointer for HITL (Day 13)
    
    Returns:
        Compiled LangGraph workflow
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("search", search_node)
    workflow.add_node("extract", extract_node)
    workflow.add_node("retry", retry_node)
    workflow.add_node("human_review", human_review_node)
    workflow.add_node("store", store_node)
    
    # Define edges
    workflow.set_entry_point("search")
    workflow.add_edge("search", "extract")
    
    # Conditional routing after extraction
    workflow.add_conditional_edges(
        "extract",
        should_continue,
        {
            "end": END,
            "retry": "retry",
            "store": "store"
        }
    )
    
    # Retry loop: refine query and search again
    workflow.add_edge("retry", "search")
    
    # Store and end
    workflow.add_edge("store", END)
    
    # Compile with optional checkpointer for HITL
    config = {}
    if checkpointer:
        config["checkpointer"] = checkpointer
        # Enable interrupt before human_review node (Day 13)
        config["interrupt_before"] = ["human_review"]
    
    return workflow.compile(**config)


# --- Example runner for testing ---
if __name__ == "__main__":
    import asyncio
    
    async def test_agent():
        print("Testing price scraper agent...")
        
        agent = build_price_agent()
        
        # Test with a specific meal
        initial_state = {
            "search_query": "Savour Foods Pulao Kabab price Islamabad",
            "iterations": 0,
            "meal_id": 1,
            "thread_id": "test_thread_1"
        }
        
        print(f"\nStarting agent with query: {initial_state['search_query']}")
        
        # Run the agent
        final_state = agent.invoke(initial_state)
        
        print("\n--- Final State ---")
        print(f"Iterations: {final_state.get('iterations')}")
        print(f"Search Query: {final_state.get('search_query')}")
        
        if final_state.get("extracted_data"):
            data = final_state["extracted_data"]
            print(f"\nExtracted Price:")
            print(f"  Restaurant: {data.restaurant_name}")
            print(f"  Meal: {data.meal_name}")
            print(f"  Price: Rs. {data.price_pkr}")
            print(f"  Confidence: {data.confidence}%")
            print(f"  Source: {data.source_url}")
        else:
            print("\nNo price data extracted")
        
        if final_state.get("retry_reason"):
            print(f"\nRetry reason: {final_state['retry_reason']}")
    
    asyncio.run(test_agent())
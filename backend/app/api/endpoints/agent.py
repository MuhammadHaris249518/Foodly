import json
import os
import sys
import uuid
from fastapi import APIRouter, Query, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

# Add the backend root directory to Python's sys.path so 'backend' can be resolved
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from backend.ai.agents.price_scraper import build_price_agent
from backend.ai.graph.checkpointer import get_checkpointer

router = APIRouter()

@router.get("/live-price")
async def get_live_price(request: Request, query: str = Query(..., description="The food item to search for")):
    """
    Server-Sent Events endpoint that triggers the AI agent to search and extract live prices.
    Used by the frontend to show real-time progress.
    """
    async def event_generator():
        thread_id = str(uuid.uuid4())
        initial_state = {
            "search_query": query,
            "iterations": 0,
            "thread_id": thread_id
        }
        config = {"configurable": {"thread_id": thread_id}}

        try:
            yield {
                "event": "message",
                "data": json.dumps({"status": "starting", "message": f"Initializing search for '{query}'...", "thread_id": thread_id})
            }
            
            async with get_checkpointer() as saver:
                agent = build_price_agent(checkpointer=saver)
                
                async for step in agent.astream(initial_state, config):
                    if await request.is_disconnected():
                        print("Client disconnected.")
                        break
                        
                    if "search" in step:
                        yield {
                            "event": "message",
                            "data": json.dumps({"status": "searching", "message": "Fetching live results from web..."})
                        }
                    elif "extract" in step:
                        yield {
                            "event": "message",
                            "data": json.dumps({"status": "extracting", "message": "AI is analyzing prices from search results..."})
                        }
                    elif "human_review" in step:
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "status": "paused", 
                                "message": "Waiting for admin approval...",
                                "thread_id": thread_id
                            })
                        }
                
                # Check if it is paused at human_review
                state = await agent.aget_state(config)
                if state and state.next and "human_review" in state.next:
                    # It's paused
                    pass
                else:
                    final_data = state.values.get("extracted_data") if state else None
                    if final_data and hasattr(final_data, "price_pkr") and getattr(final_data, "price_pkr", 0) > 0:
                        result = {
                            "restaurant": final_data.restaurant_name,
                            "meal": final_data.meal_name,
                            "price_pkr": final_data.price_pkr,
                            "confidence": final_data.confidence
                        }
                        yield {
                            "event": "message",
                            "data": json.dumps({"status": "complete", "message": "Price found and saved!", "data": result})
                        }
                    else:
                        yield {
                            "event": "message",
                            "data": json.dumps({"status": "failed", "message": "Could not extract a valid price from the web."})
                        }
                
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"status": "error", "message": str(e)})
            }
            
    return EventSourceResponse(event_generator())

class ResumeRequest(BaseModel):
    action: str  # "approve" or "reject"

@router.post("/resume/{thread_id}")
async def resume_agent(thread_id: str, payload: ResumeRequest, background_tasks: BackgroundTasks):
    if payload.action not in ["approve", "reject"]:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'")
        
    async def process_resume():
        async with get_checkpointer() as saver:
            agent = build_price_agent(checkpointer=saver)
            config = {"configurable": {"thread_id": thread_id}}
            
            state = await agent.aget_state(config)
            if not state or not state.next:
                return
                
            if payload.action == "reject":
                # Clear extracted data so store_node skips saving it
                await agent.aupdate_state(config, {"extracted_data": None})
                
            # Resume the graph from where it paused
            await agent.ainvoke(None, config)

    background_tasks.add_task(process_resume)
    return {"status": "resumed", "thread_id": thread_id, "action": payload.action}

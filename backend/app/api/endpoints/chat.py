"""
Conversational assistant endpoint — SSE streaming (Sprint 3).
"""
import json
import os
import sys
import uuid
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import HumanMessage

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from backend.ai.graph.assistant_graph import build_assistant_graph
from backend.ai.graph.checkpointer import get_checkpointer
from ...core.rate_limit import limiter
from ...services.auth import get_current_user
from ...models.user import User

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    lat: float | None = None
    lng: float | None = None
    thread_id: str | None = None


@router.post("")
@limiter.limit("10/minute")  # AI calls are expensive — same limit tier as /agent/live-price
async def chat(
    request: Request,
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
):
    thread_id = payload.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    location_context = ""
    if payload.lat is not None and payload.lng is not None:
        location_context = f"\n[User's current location: lat={payload.lat}, lng={payload.lng}]"
    user_message = payload.message + location_context

    async def event_generator():
        try:
            yield {"event": "message", "data": json.dumps({"type": "thinking", "thread_id": thread_id})}

            async with get_checkpointer() as saver:
                agent = build_assistant_graph(checkpointer=saver)

                async for event in agent.astream_events(
                    {"messages": [HumanMessage(content=user_message)]},
                    config=config,
                    version="v2",
                ):
                    if await request.is_disconnected():
                        break

                    kind = event["event"]

                    if kind == "on_tool_start":
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "type": "tool_call",
                                "tool": event["name"],
                                "args": event["data"].get("input", {}),
                            }),
                        }
                    elif kind == "on_tool_end":
                        yield {
                            "event": "message",
                            "data": json.dumps({
                                "type": "tool_result",
                                "tool": event["name"],
                                "result": str(event["data"].get("output", ""))[:2000],
                            }),
                        }
                    elif kind == "on_chat_model_stream":
                        chunk = event["data"].get("chunk")
                        text = getattr(chunk, "content", None) if chunk else None
                        if text:
                            yield {"event": "message", "data": json.dumps({"type": "token", "text": text})}

            yield {"event": "message", "data": json.dumps({"type": "done", "thread_id": thread_id})}

        except Exception:
            # Matches the existing degrade-not-crash pattern used elsewhere in ai/ —
            # full safe_invoke() standardization is Sprint 8's job.
            yield {
                "event": "message",
                "data": json.dumps({
                    "type": "error",
                    "message": "I'm having trouble connecting. Try again shortly.",
                }),
            }

    return EventSourceResponse(event_generator())
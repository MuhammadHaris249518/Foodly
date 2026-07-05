"""
Conversational food assistant — LangGraph ReAct agent (Sprint 3).
"""
import os
from langgraph.prebuilt import create_react_agent
from langchain_groq import ChatGroq

from backend.ai.tools.foodly_tools import (
    search_nearby_meals,
    filter_meals,
    get_meal_insight,
    get_price_trend,
    semantic_search_meals,
)

SYSTEM_PROMPT = """You are Foodly's food discovery assistant for Islamabad and Rawalpindi, Pakistan.

Scope: you ONLY help with finding meals, restaurants, prices, and value comparisons in
Islamabad/Rawalpindi. If asked about anything outside this scope (general knowledge,
other cities, unrelated topics), politely decline and redirect the conversation back
to food discovery.

When the user gives a budget or location, use your tools to search rather than guessing.
Prefer semantic_search_meals for vague/descriptive requests ("something spicy") and
search_nearby_meals when a location is available. Use filter_meals to narrow results
by category exclusion or confidence. Use get_meal_insight or get_price_trend only when
the user asks about value or price history for a specific meal.

Keep responses concise and grounded only in tool results — never invent prices or meals."""


def get_assistant_llm() -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment")
    return ChatGroq(api_key=api_key, model="llama-3.3-70b-versatile", temperature=0.4)


def build_assistant_graph(checkpointer=None):
    """
    Build the ReAct assistant graph.

    Args:
        checkpointer: LangGraph checkpointer for multi-turn memory (same
            AsyncPostgresSaver pattern used by the price agent's HITL flow).
    """
    llm = get_assistant_llm()
    tools = [
        search_nearby_meals,
        filter_meals,
        get_meal_insight,
        get_price_trend,
        semantic_search_meals,
    ]
    return create_react_agent(
        model=llm,
        tools=tools,
        checkpointer=checkpointer,
        prompt=SYSTEM_PROMPT,
    )
"""
LangChain tools for the conversational food assistant (Sprint 3).

Design note: every tool here is a thin wrapper around existing repository/
service/chain functions — no new DB access patterns are introduced. Each
tool opens its own short-lived SessionLocal() per call (not shared across
concurrent tool invocations), consistent with the thread-safety lesson
from the RAG insight chain fix.
"""
import asyncio
from typing import Optional, List, Dict, Any
from langchain_core.tools import tool

from backend.app.core.database import SessionLocal
from backend.app.repositories.meal import meal_repository
from backend.app.services.embeddings import embed_query_async
from backend.app.services.meal import _extract_category  # reuse existing category heuristic
from backend.ai.chains.insight_chain import generate_rag_insight


def _meal_to_dict(meal) -> Dict[str, Any]:
    return {
        "id": meal.id,
        "name": meal.name,
        "price": meal.price,
        "location": meal.location,
        "confidence": meal.confidence,
        "description": meal.description,
    }


@tool
async def search_nearby_meals(
    lat: float,
    lng: float,
    radius_km: float = 3.0,
    max_price: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Search for meals near a GPS location, optionally under a price ceiling.
    Use when the user gives (or you already have) a location and wants nearby options.
    """
    def _query():
        db = SessionLocal()
        try:
            # Pass max_price through as-is (including None) — do NOT convert to 0.
            # meal_service.get_nearby_meals does `budget or 0`, which would make
            # "no budget given" filter out every meal (price <= 0). Talking to the
            # repository directly avoids inheriting that bug.
            meals = meal_repository.list_nearby(
                db, lat=lat, lng=lng, radius_km=radius_km, budget=max_price
            )
            return [_meal_to_dict(m) for m in meals]
        finally:
            db.close()

    return await asyncio.to_thread(_query)


@tool
async def filter_meals(
    meals: List[Dict[str, Any]],
    exclude_category: Optional[str] = None,
    min_confidence: int = 50,
) -> List[Dict[str, Any]]:
    """Filter a list of meals (from search_nearby_meals or semantic_search_meals) by
    excluding a food category (e.g. 'biryani') and/or requiring a minimum confidence score.
    Category matching reuses the same keyword heuristic as the AI insight system —
    there is no dedicated category column in the database.
    """
    def _is_excluded(meal: Dict[str, Any]) -> bool:
        if not exclude_category:
            return False
        detected = _extract_category(meal.get("name", ""), meal.get("description") or "")
        return detected == exclude_category.lower().strip()

    return [
        m for m in meals
        if not _is_excluded(m) and (m.get("confidence") or 0) >= min_confidence
    ]


@tool
async def get_meal_insight(meal_id: int) -> str:
    """Get the AI-generated value insight (verdict, summary, tip) for a specific meal by ID."""
    def _fetch_meal():
        db = SessionLocal()
        try:
            return meal_repository.get_by_id(db, meal_id)
        finally:
            db.close()

    meal = await asyncio.to_thread(_fetch_meal)
    if not meal:
        return f"No meal found with id {meal_id}."

    db = SessionLocal()
    try:
        category = _extract_category(meal.name, meal.description or "")
        insight = await generate_rag_insight(
            db=db,
            meal_id=meal.id,
            meal_name=meal.name,
            meal_price=meal.price,
            meal_location=meal.location or "Islamabad",
            meal_description=meal.description or "",
            meal_category=category,
            meal_embedding=meal.embedding,
        )
        if insight:
            return f"{insight.verdict.replace('_', ' ').title()}: {insight.summary} Tip: {insight.tip}"
        return "AI insight is temporarily unavailable for this meal."
    finally:
        db.close()


@tool
async def get_price_trend(meal_id: int) -> str:
    """Get the price trend for a meal — rising, falling, or stable — based on approved price reports."""
    def _fetch():
        db = SessionLocal()
        try:
            return meal_repository.get_approved_reports(db, meal_id)
        finally:
            db.close()

    reports = await asyncio.to_thread(_fetch)
    if len(reports) < 2:
        return "Not enough price history yet to determine a trend."

    first_price = reports[0].reported_price
    last_price = reports[-1].reported_price
    if last_price > first_price * 1.05:
        return f"Price trend: rising (from PKR {first_price} to PKR {last_price})."
    if last_price < first_price * 0.95:
        return f"Price trend: falling (from PKR {first_price} to PKR {last_price})."
    return f"Price trend: stable (around PKR {last_price})."


@tool
async def semantic_search_meals(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Semantically search meals by description, cuisine, or vibe (e.g. 'spicy street food').
    Use when the request isn't a literal meal name.
    """
    embedding = await embed_query_async(query)
    if not embedding:
        return []

    def _query():
        db = SessionLocal()
        try:
            meals = meal_repository.list_paginated(db, limit=limit, query_embedding=embedding)
            return [_meal_to_dict(m) for m in meals]
        finally:
            db.close()

    return await asyncio.to_thread(_query)
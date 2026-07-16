from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
from fastapi import HTTPException
import asyncio
import hashlib
import json
import logging

from ..schemas import meal as meal_schema
from ..schemas.meal import InsightResponse
from ..repositories.meal import meal_repository
from .embeddings import embed_query_async
from ai.agents.agents import generate_value_insight
from ai.chains.insight_chain import generate_rag_insight
from ..core.cache import get_cached, set_cached

logger = logging.getLogger(__name__)


async def _cached_insight_legacy(name: str, price: float, location: str, description: str) -> str:
    """Legacy insight generation (Day 9) - kept as fallback."""
    cache_key = f"ai_insight_legacy:{hashlib.md5(f'{name}{price}{location}'.encode()).hexdigest()}"
    cached_val = await get_cached(cache_key)
    if cached_val:
        return cached_val
        
    insight = await generate_value_insight(name=name, price=price, location=location, description=description)
    await set_cached(cache_key, insight, ttl_seconds=86400)
    return insight


async def _cached_insight(name: str, price: float, location: str, description: str) -> str:
    """Legacy wrapper for backward compatibility."""
    return await _cached_insight_legacy(name, price, location, description)


async def _cached_rag_insight(db: Session, meal_id: int, meal) -> Optional[InsightResponse]:
    """
    Day 10: RAG-grounded insight with caching.
    
    Args:
        db: Database session
        meal_id: Meal ID
        meal: Meal object from database
    
    Returns:
        InsightResponse with structured verdict and market context
    """
    # Check cache first
    cache_key = f"insight:{meal_id}:{meal.price}"
    cached_val = await get_cached(cache_key)
    if cached_val:
        logger.info(f"Cache HIT for insight: meal {meal_id}")
        # Parse cached JSON back to InsightResponse
        if isinstance(cached_val, str):
            cached_val = json.loads(cached_val)
        return InsightResponse(**cached_val)
    
    # Cache miss - generate RAG insight
    logger.info(f"Cache MISS for insight: meal {meal_id} - generating RAG insight")
    
    # Extract category from location (simple heuristic)
    # In production, you'd have a proper category field
    category = _extract_category(meal.name, meal.description)
    
    # Generate RAG insight
    insight = await generate_rag_insight(
        db=db,
        meal_id=meal_id,
        meal_name=meal.name,
        meal_price=meal.price,
        meal_location=meal.location or "Islamabad",
        meal_description=meal.description or "",
        meal_category=category,
        meal_embedding=meal.embedding
    )
    
    if insight:
        # Cache for 24 hours (86400 seconds)
        # Cache key includes price so it invalidates when price changes
        await set_cached(
            cache_key,
            insight.model_dump_json(),
            ttl_seconds=86400
        )
        logger.info(f"Cached RAG insight for meal {meal_id}")
        return insight
    else:
        # Fallback to legacy insight if RAG fails
        logger.warning(f"RAG insight failed for meal {meal_id}, falling back to legacy")
        fallback_text = await _cached_insight_legacy(
            name=meal.name,
            price=meal.price,
            location=meal.location or "Islamabad",
            description=meal.description or ""
        )
        
        # Return as InsightResponse with default values
        return InsightResponse(
            verdict="fair",
            summary=fallback_text,
            tip="Check back later for updated insights",
            price_percentile=50,
            confidence=60
        )


def _extract_category(name: str, description: str = "") -> str:
    """
    Extract meal category from name/description.
    Simple keyword matching - in production, use a proper category field.
    """
    text = f"{name} {description}".lower()
    
    categories = {
        "biryani": ["biryani", "biriyani"],
        "karahi": ["karahi", "qorma"],
        "fast_food": ["burger", "pizza", "fries", "shawarma", "sandwich"],
        "bbq": ["bbq", "tikka", "seekh", "kebab", "grill"],
        "chinese": ["chinese", "fried rice", "noodles", "manchurian"],
        "dessert": ["ice cream", "kulfi", "falooda", "sweet", "dessert"],
        "breakfast": ["breakfast", "paratha", "chai", "tea", "omelet"],
        "pulao": ["pulao", "pilao", "biryani pulao"]
    }
    
    for category, keywords in categories.items():
        if any(keyword in text for keyword in keywords):
            return category
    
    return "general"

class MealService:
    @staticmethod
    async def get_meals(
        db: Session, skip: int = 0, limit: int = 100, budget: Optional[float] = None, search: Optional[str] = None
    ) -> List[Any]:
        if not search:
            return meal_repository.list_paginated(db=db, skip=skip, limit=limit, budget=budget)
            
        hash_str = f"search:{search}:{budget}:{skip}:{limit}"
        cache_key = f"search_cache:{hashlib.md5(hash_str.encode()).hexdigest()}"
        
        cached_meals = await get_cached(cache_key)
        if cached_meals:
            return cached_meals
            
        try:
            from ai.chains.query_expansion_chain import expand_query
            
            expanded_terms = await expand_query(search)
            all_terms = [search] + expanded_terms
            
            # Run embed_query_async in parallel for all terms
            embeddings = await asyncio.gather(*[embed_query_async(t) for t in all_terms])
            
            # Filter out None embeddings
            valid_embeddings = [e for e in embeddings if e is not None]
            
            if valid_embeddings:
                meals = meal_repository.vector_union_search(
                    db=db, embeddings=valid_embeddings, limit=limit, budget=budget
                )
                serialized = [meal_schema.Meal.model_validate(m).model_dump() for m in meals]
                await set_cached(cache_key, serialized, ttl_seconds=3600)
                return meals
        except Exception as e:
            print(f"Error during semantic search: {e}")
            
        # Fallback to simple ILIKE search if embedding/expansion fails or returns no embeddings
        search_fmt = f"%{search}%"
        meals = meal_repository.list_paginated(
            db=db, skip=skip, limit=limit, budget=budget, search_fmt=search_fmt
        )
        serialized = [meal_schema.Meal.model_validate(m).model_dump() for m in meals]
        await set_cached(cache_key, serialized, ttl_seconds=3600)
        return meals

    @staticmethod
    def get_nearby_meals(
        db: Session, lat: float, lng: float, radius_km: float = 3.0,
        budget: Optional[float] = None, search: Optional[str] = None
    ) -> List[meal_schema.Meal]:
        if radius_km <= 0:
            raise HTTPException(status_code=400, detail="radius_km must be greater than 0")
            
        search_fmt = f"%{search}%" if search else None
        return meal_repository.list_nearby(
            db=db, lat=lat, lng=lng, radius_km=radius_km, 
            budget=budget, search_fmt=search_fmt or ""
        )

    @staticmethod
    def create_meal(db: Session, meal_data: meal_schema.MealCreate):
        return meal_repository.create(db=db, meal_data=meal_data)

    @staticmethod
    def save_meal(db: Session, meal_id: int, user_id: int):
        meal = meal_repository.get_by_id(db, meal_id)
        if not meal:
            raise HTTPException(status_code=404, detail="Meal not found")
        meal_repository.save_for_user(db, meal_id, user_id)
        return meal

    @staticmethod
    def unsave_meal(db: Session, meal_id: int, user_id: int):
        meal_repository.unsave_for_user(db, meal_id, user_id)

    @staticmethod
    async def get_meal_detail(db: Session, meal_id: int) -> Dict[str, Any]:
        meal = meal_repository.get_by_id(db, meal_id)
        if not meal:
            raise HTTPException(status_code=404, detail="Meal not found")
            
        approved_reports = meal_repository.get_approved_reports(db, meal_id)
        
        monthly: dict = defaultdict(list)
        for r in approved_reports:
            if r.created_at:
                key = r.created_at.strftime("%b %Y")
                monthly[key].append(r.reported_price)

        price_history = [
            {"month": month, "price": round(sum(prices) / len(prices))}
            for month, prices in monthly.items()
        ]

        current_month = datetime.now().strftime("%b %Y")
        if not any(p["month"] == current_month for p in price_history):
            price_history.append({"month": current_month, "price": meal.price})

        try:
            # Day 10: Use RAG-grounded insight
            rag_insight = await asyncio.wait_for(
                _cached_rag_insight(db, meal_id, meal),
                timeout=10.0  # RAG takes longer (DB queries + LLM)
            )
            
            if rag_insight:
                # Format as dict for API response
                ai_insight = {
                    "type": "rag_insight",
                    "data": rag_insight.model_dump()
                }
            else:
                # Fallback to legacy insight
                ai_insight = await asyncio.wait_for(
                    _cached_insight(
                        meal.name,
                        meal.price,
                        meal.location,
                        meal.description or ""
                    ),
                    timeout=3.0
                )
                ai_insight = {"type": "legacy", "data": ai_insight}
                
        except asyncio.TimeoutError:
            ai_insight = {"type": "error", "data": "AI analysis timed out. This meal looks promising!"}
        except Exception as e:
            logger.error(f"Insight generation failed: {e}")
            ai_insight = {"type": "error", "data": "AI analysis temporarily unavailable."}

        return {
            "meal": {
                "id": meal.id,
                "name": meal.name,
                "price": meal.price,
                "location": meal.location,
                "confidence": meal.confidence,
                "image_url": meal.image_url,
                "description": meal.description
            },
            "price_history": price_history,
            "ai_insight": ai_insight
        }

meal_service = MealService()

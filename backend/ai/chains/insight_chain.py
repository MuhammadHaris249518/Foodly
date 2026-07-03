"""
Grounded AI Insight Chain with RAG - Day 10 Implementation
Retrieves market context before generating insights for accurate, data-driven verdicts.

Workflow:
1. Retrieve similar meals (pgvector similarity search)
2. Fetch sector statistics (avg/min/max prices)
3. Fetch price history (last 10 approved reports)
4. Build grounded prompt with all context
5. Generate structured insight with verdict
"""
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from sqlalchemy.exc import SQLAlchemyError
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from pydantic import BaseModel, Field
import os
import logging
logger = logging.getLogger(__name__)

# Import models and schemas
from backend.app.models.meal import Meal
from backend.app.models.pending_verification import PendingVerification
from backend.app.schemas.meal import InsightResponse


# --- Helper Functions for Context Retrieval ---

def retrieve_similar_meals(
    db: Session,
    meal_id: int,
    category: str,
    embedding: Optional[List[float]],
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Retrieve top 5 similar meals by vector similarity.

    NOTE: `category` is accepted for signature compatibility with callers
    (services/meal.py passes a heuristically-derived category), but is not
    used for SQL filtering — the `meals` table has no `category` column.
    Similarity is determined purely by pgvector cosine distance on
    `Meal.embedding`, which already captures semantic/category signal.

    Args:
        db: Database session
        meal_id: Current meal ID (to exclude from results)
        category: Reserved for future use (see note above)
        embedding: 1536-dim vector embedding
        limit: Number of similar meals to return

    Returns:
        List of similar meals with id, name, price, location, similarity_score
    """
    if not embedding:
        return []

    try:
        # Pass the raw embedding list directly — matches the working pattern
        # used in MealRepository.vector_union_search. Do NOT stringify; that
        # bypasses the pgvector parameter adapter.
        query = db.query(
            Meal.id,
            Meal.name,
            Meal.price,
            Meal.location,
            Meal.confidence,
            (1 - Meal.embedding.op('<=>')(embedding)).label('similarity')
        ).filter(
            Meal.embedding.isnot(None),
            Meal.id != meal_id,  # Exclude current meal
        ).order_by(
            desc('similarity')
        ).limit(limit)

        results = query.all()

        return [
            {
                "id": r.id,
                "name": r.name,
                "price": r.price,
                "location": r.location,
                "confidence": r.confidence,
                "similarity": round(float(r.similarity), 3)
            }
            for r in results
        ]

    except SQLAlchemyError:
        logger.exception(
            "retrieve_similar_meals failed (meal_id=%s, category=%s)", meal_id, category
        )
        return []


def fetch_sector_stats(
    db: Session,
    category: str,
    sector: str
) -> Dict[str, Any]:
    """
    Fetch price statistics for meals in a specific sector.

    NOTE: `category` is reserved for future use — see retrieve_similar_meals
    docstring. Filtering here is scoped by `location` (sector) and
    `confidence` only, both of which exist on the Meal model.

    Args:
        db: Database session
        category: Reserved for future use (see note above)
        sector: Location sector (e.g., "F-7", "G-9")

    Returns:
        Dict with avg_price, min_price, max_price, meal_count
    """
    try:
        query = db.query(
            func.avg(Meal.price).label('avg_price'),
            func.min(Meal.price).label('min_price'),
            func.max(Meal.price).label('max_price'),
            func.count(Meal.id).label('meal_count')
        ).filter(
            Meal.location.ilike(f"%{sector}%"),
            Meal.confidence >= 50  # Only consider reliable prices
        )

        result = query.first()

        if result and result.meal_count > 0:
            return {
                "avg_price": round(float(result.avg_price), 0),
                "min_price": round(float(result.min_price), 0),
                "max_price": round(float(result.max_price), 0),
                "meal_count": result.meal_count
            }

        # Fallback: search without sector restriction
        query_fallback = db.query(
            func.avg(Meal.price).label('avg_price'),
            func.min(Meal.price).label('min_price'),
            func.max(Meal.price).label('max_price'),
            func.count(Meal.id).label('meal_count')
        ).filter(
            Meal.confidence >= 50
        )

        result_fallback = query_fallback.first()

        if result_fallback and result_fallback.meal_count > 0:
            return {
                "avg_price": round(float(result_fallback.avg_price), 0),
                "min_price": round(float(result_fallback.min_price), 0),
                "max_price": round(float(result_fallback.max_price), 0),
                "meal_count": result_fallback.meal_count,
                "note": f"Across all sectors (no data for {sector})"
            }

        return {
            "avg_price": 0,
            "min_price": 0,
            "max_price": 0,
            "meal_count": 0
        }

    except SQLAlchemyError:
        logger.exception(
            "fetch_sector_stats failed (category=%s, sector=%s)", category, sector
        )
        return {
            "avg_price": 0,
            "min_price": 0,
            "max_price": 0,
            "meal_count": 0
        }


def fetch_price_history(
    db: Session,
    meal_id: int,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Fetch last N approved price reports for a meal.

    Args:
        db: Database session
        meal_id: Meal ID
        limit: Number of historical reports to fetch

    Returns:
        List of {price, date, reporter}
    """
    try:
        reports = db.query(PendingVerification).filter(
            PendingVerification.meal_id == meal_id,
            PendingVerification.status == "approved"
        ).order_by(
            desc(PendingVerification.created_at)
        ).limit(limit).all()

        return [
            {
                "price": r.reported_price,
                "date": r.created_at.strftime("%Y-%m-%d") if r.created_at else "unknown",
                "reporter": r.reporter_name or "anonymous"
            }
            for r in reports
        ]

    except SQLAlchemyError:
        logger.exception("fetch_price_history failed (meal_id=%s)", meal_id)
        return []


def calculate_price_percentile(
    current_price: float,
    similar_prices: List[float]
) -> int:
    """
    Calculate what percentile the current price is compared to similar meals.

    Returns:
        Percentile (0-100). Lower = better deal.
        Example: 25 means cheaper than 75% of similar meals
    """
    if not similar_prices:
        return 50  # Default to middle if no data

    cheaper_count = sum(1 for p in similar_prices if p > current_price)
    percentile = int((cheaper_count / len(similar_prices)) * 100)

    return min(100, max(0, percentile))


# --- Prompt Template ---

INSIGHT_PROMPT = PromptTemplate(
    input_variables=[
        "meal_name", "price", "location", "description",
        "similar_meals", "sector_stats", "price_history",
        "price_percentile", "cheaper_percentage"
    ],
    template="""You are a local food expert in Islamabad, Pakistan analyzing meal prices.

MEAL DETAILS:
- Name: {meal_name}
- Price: PKR {price}
- Location: {location}
- Description: {description}

MARKET CONTEXT:

1. Similar Meals (same category, vector similarity):
{similar_meals}

2. Sector Statistics:
{sector_stats}

3. Price History (recent approved reports):
{price_history}

4. Price Percentile: This meal is at the {price_percentile}th percentile (cheaper than {cheaper_percentage}% of similar meals)

TASK:
Analyze if this is a good value and provide:
1. **Verdict**: Choose ONE: "best_deal", "good_value", "fair", or "overpriced"
   - best_deal: Significantly cheaper than average (percentile < 25)
   - good_value: Below average price (percentile 25-50)
   - fair: Around average (percentile 50-75)
   - overpriced: Above average (percentile > 75)

2. **Summary**: 1-2 sentences grounded in the actual data above. Reference specific prices and comparisons.

3. **Tip**: One actionable tip for the user (e.g., "Go before 2pm for smaller crowds", "Try their lunch deal")

4. **Price Percentile**: Use the calculated value: {price_percentile}

5. **Confidence**: Your confidence in this analysis (0-100) based on data quality

Return ONLY valid JSON with these exact keys: verdict, summary, tip, price_percentile, confidence

Example format:
{{
  "verdict": "good_value",
  "summary": "At PKR 350, this biryani is 15% below the F-7 sector average of PKR 410. Similar meals in the area range from PKR 300-500.",
  "tip": "Visit during lunch hours (12-2pm) for a complimentary chai",
  "price_percentile": 35,
  "confidence": 85
}}

JSON Response:"""
)


# --- Main Insight Chain ---

def build_insight_chain(db: Session):
    """
    Build the RAG-grounded insight chain.

    Args:
        db: SQLAlchemy database session

    Returns:
        LangChain LCEL chain
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=api_key,
        temperature=0.7,
        max_tokens=300
    )

    chain = (
        RunnableParallel({
            # `x["meal"]` is a plain dict built in generate_rag_insight(),
            # not an ORM object — access via key, not attribute.
            "meal_name": lambda x: x["meal"]["name"],
            "price": lambda x: x["meal"]["price"],
            "location": lambda x: x["meal"]["location"] or "Islamabad",
            "description": lambda x: x["meal"]["description"] or "No description",
            "similar_meals": lambda x: _format_similar_meals(x.get("similar_meals", [])),
            "sector_stats": lambda x: _format_sector_stats(x.get("sector_stats", {})),
            "price_history": lambda x: _format_price_history(x.get("price_history", [])),
            "price_percentile": lambda x: x.get("price_percentile", 50),
            "cheaper_percentage": lambda x: 100 - x.get("price_percentile", 50),
        })
        | INSIGHT_PROMPT
        | llm
        | JsonOutputParser()
        | _validate_insight_output
    )

    return chain


def _format_similar_meals(meals: List[Dict]) -> str:
    """Format similar meals for prompt."""
    if not meals:
        return "No similar meals found in database."

    lines = []
    for i, m in enumerate(meals[:5], 1):
        lines.append(f"{i}. {m['name']} - PKR {m['price']} ({m['location']}) - {m['similarity']*100:.0f}% similar")

    return "\n".join(lines)


def _format_sector_stats(stats: Dict) -> str:
    """Format sector statistics for prompt."""
    if stats.get("meal_count", 0) == 0:
        return "No sector data available."

    note = f"\nNote: {stats['note']}" if "note" in stats else ""

    return f"""Average Price: PKR {stats['avg_price']}
Price Range: PKR {stats['min_price']} - PKR {stats['max_price']}
Meals in sector: {stats['meal_count']}{note}"""


def _format_price_history(history: List[Dict]) -> str:
    """Format price history for prompt."""
    if not history:
        return "No price history available."

    lines = []
    for h in history[:5]:
        lines.append(f"- PKR {h['price']} on {h['date']} (reported by {h['reporter']})")

    return "\n".join(lines)


def _validate_insight_output(data: Dict) -> Dict:
    """Validate and sanitize insight output from LLM."""
    required_fields = ["verdict", "summary", "tip", "price_percentile", "confidence"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    valid_verdicts = ["best_deal", "good_value", "fair", "overpriced"]
    if data["verdict"] not in valid_verdicts:
        data["verdict"] = "fair"

    data["price_percentile"] = max(0, min(100, int(data["price_percentile"])))
    data["confidence"] = max(0, min(100, int(data["confidence"])))

    if len(data["summary"]) > 300:
        data["summary"] = data["summary"][:297] + "..."
    if len(data["tip"]) > 200:
        data["tip"] = data["tip"][:197] + "..."

    return data


# --- Main Function to Generate Insight ---

async def generate_rag_insight(
    db: Session,
    meal_id: int,
    meal_name: str,
    meal_price: float,
    meal_location: str,
    meal_description: str = "",
    meal_category: str = "",
    meal_embedding: Optional[List[float]] = None
) -> Optional[InsightResponse]:
    """
    Generate RAG-grounded AI insight for a meal.

    Args:
        db: Database session
        meal_id: Meal ID
        meal_name: Meal name
        meal_price: Current price in PKR
        meal_location: Restaurant location/sector
        meal_description: Meal description
        meal_category: Heuristic category label (see retrieve_similar_meals note)
        meal_embedding: 1536-dim embedding for similarity search

    Returns:
        InsightResponse with verdict, summary, tip, price_percentile, confidence
        or None if generation fails
    """
    try:
        logger.info(f"Generating RAG insight for meal {meal_id}: {meal_name}")

        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        with ThreadPoolExecutor(max_workers=3) as executor:
            loop = asyncio.get_event_loop()

            similar_future = loop.run_in_executor(
                executor,
                retrieve_similar_meals,
                db, meal_id, meal_category, meal_embedding, 5
            )

            sector_future = loop.run_in_executor(
                executor,
                fetch_sector_stats,
                db, meal_category, meal_location
            )

            history_future = loop.run_in_executor(
                executor,
                fetch_price_history,
                db, meal_id, 10
            )

            similar_meals, sector_stats, price_history = await asyncio.gather(
                similar_future, sector_future, history_future
            )

        similar_prices = [m["price"] for m in similar_meals]
        price_percentile = calculate_price_percentile(meal_price, similar_prices)

        context = {
            "meal": {
                "name": meal_name,
                "price": meal_price,
                "location": meal_location,
                "description": meal_description
            },
            "similar_meals": similar_meals,
            "sector_stats": sector_stats,
            "price_history": price_history,
            "price_percentile": price_percentile
        }

        chain = build_insight_chain(db)
        result = await chain.ainvoke(context)

        insight = InsightResponse(**result)

        logger.info(
            f"Generated insight for {meal_name}: "
            f"verdict={insight.verdict}, percentile={insight.price_percentile}%"
        )

        return insight

    except Exception as e:
        logger.error(f"Failed to generate RAG insight for meal {meal_id}: {e}", exc_info=True)
        return None


# --- Singleton chain for reuse ---

_insight_chain_singleton = None

def get_insight_chain_singleton(db: Session):
    """Get or create insight chain singleton for a DB session."""
    global _insight_chain_singleton
    if _insight_chain_singleton is None:
        _insight_chain_singleton = build_insight_chain(db)
    return _insight_chain_singleton
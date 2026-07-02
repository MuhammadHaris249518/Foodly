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
    
    Args:
        db: Database session
        meal_id: Current meal ID (to exclude from results)
        category: Meal category for filtering
        embedding: 1536-dim vector embedding
        limit: Number of similar meals to return
    
    Returns:
        List of similar meals with id, name, price, location, similarity_score
    """
    if not embedding:
        return []
    
    try:
        # Convert embedding list to string for SQLAlchemy
        embedding_str = str(embedding)
        
        # Query using pgvector cosine similarity
        # Using <=> operator for cosine distance
        query = db.query(
            Meal.id,
            Meal.name,
            Meal.price,
            Meal.location,
            Meal.confidence,
            # Calculate cosine similarity (1 - cosine_distance)
            (1 - Meal.embedding.op('<=>')(embedding_str)).label('similarity')
        ).filter(
            Meal.embedding.isnot(None),
            Meal.id != meal_id,  # Exclude current meal
            Meal.category == category  # Same category
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
    
    except Exception as e:
        logger.error(f"Failed to retrieve similar meals: {e}")
        return []


def fetch_sector_stats(
    db: Session,
    category: str,
    sector: str
) -> Dict[str, Any]:
    """
    Fetch price statistics for a specific category in a sector.
    
    Args:
        db: Database session
        category: Meal category (e.g., "biryani", "karahi")
        sector: Location sector (e.g., "F-7", "G-9")
    
    Returns:
        Dict with avg_price, min_price, max_price, meal_count
    """
    try:
        # Query for meals in the same category and sector
        # Note: sector is stored in location field, so we use ILIKE for partial match
        query = db.query(
            func.avg(Meal.price).label('avg_price'),
            func.min(Meal.price).label('min_price'),
            func.max(Meal.price).label('max_price'),
            func.count(Meal.id).label('meal_count')
        ).filter(
            Meal.category == category,
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
        else:
            # Fallback: search without sector restriction
            query_fallback = db.query(
                func.avg(Meal.price).label('avg_price'),
                func.min(Meal.price).label('min_price'),
                func.max(Meal.price).label('max_price'),
                func.count(Meal.id).label('meal_count')
            ).filter(
                Meal.category == category,
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
    
    except Exception as e:
        logger.error(f"Failed to fetch sector stats: {e}")
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
        List of {reported_price, created_at, reporter_name}
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
    
    except Exception as e:
        logger.error(f"Failed to fetch price history: {e}")
        return []


def calculate_price_percentile(
    current_price: float,
    similar_prices: List[float]
) -> int:
    """
    Calculate what percentile the current price is compared to similar meals.
    
    Args:
        current_price: The meal's current price
        similar_prices: List of prices from similar meals
    
    Returns:
        Percentile (0-100). Lower = better deal.
        Example: 25 means cheaper than 75% of similar meals
    """
    if not similar_prices:
        return 50  # Default to middle if no data
    
    # Count how many similar meals are more expensive
    cheaper_count = sum(1 for p in similar_prices if p > current_price)
    percentile = int((cheaper_count / len(similar_prices)) * 100)
    
    return min(100, max(0, percentile))


# --- Prompt Template ---

INSIGHT_PROMPT = PromptTemplate(
    input_variables=[
        "meal_name", "price", "location", "description",
        "similar_meals", "sector_stats", "price_history", "price_percentile"
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

4. Price Percentile: This meal is at the {price_percentile}th percentile (cheaper than {100-price_percentile}% of similar meals)

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
    
    This is a factory function that takes a DB session and returns a chain
    that can be invoked with meal data.
    
    Args:
        db: SQLAlchemy database session
    
    Returns:
        LangChain LCEL chain
    """
    # Get LLM
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=api_key,
        temperature=0.7,
        max_tokens=300
    )
    
    # Create the chain
    chain = (
        RunnableParallel({
            "meal_name": lambda x: x["meal"].name,
            "price": lambda x: x["meal"].price,
            "location": lambda x: x["meal"].location or "Islamabad",
            "description": lambda x: x["meal"].description or "No description",
            "similar_meals": lambda x: _format_similar_meals(x.get("similar_meals", [])),
            "sector_stats": lambda x: _format_sector_stats(x.get("sector_stats", {})),
            "price_history": lambda x: _format_price_history(x.get("price_history", [])),
            "price_percentile": lambda x: x.get("price_percentile", 50)
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
    # Ensure required fields exist
    required_fields = ["verdict", "summary", "tip", "price_percentile", "confidence"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate verdict
    valid_verdicts = ["best_deal", "good_value", "fair", "overpriced"]
    if data["verdict"] not in valid_verdicts:
        data["verdict"] = "fair"
    
    # Validate percentile
    data["price_percentile"] = max(0, min(100, int(data["price_percentile"])))
    
    # Validate confidence
    data["confidence"] = max(0, min(100, int(data["confidence"])))
    
    # Truncate summary and tip if too long
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
    
    This is the main entry point for Day 10 RAG insight generation.
    It retrieves market context, builds a grounded prompt, and returns
    a structured insight with verdict.
    
    Args:
        db: Database session
        meal_id: Meal ID
        meal_name: Meal name
        meal_price: Current price in PKR
        meal_location: Restaurant location/sector
        meal_description: Meal description
        meal_category: Meal category (for similar meals search)
        meal_embedding: 1536-dim embedding for similarity search
    
    Returns:
        InsightResponse with verdict, summary, tip, price_percentile, confidence
        or None if generation fails
    """
    try:
        logger.info(f"Generating RAG insight for meal {meal_id}: {meal_name}")
        
        # Step 1: Retrieve context in parallel
        import asyncio
        from concurrent.futures import ThreadPoolExecutor
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            loop = asyncio.get_event_loop()
            
            # Run DB queries in parallel (they're blocking)
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
            
            # Wait for all to complete
            similar_meals, sector_stats, price_history = await asyncio.gather(
                similar_future, sector_future, history_future
            )
        
        # Step 2: Calculate price percentile
        similar_prices = [m["price"] for m in similar_meals]
        price_percentile = calculate_price_percentile(meal_price, similar_prices)
        
        # Step 3: Build context dict
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
        
        # Step 4: Build and invoke chain
        chain = build_insight_chain(db)
        result = await chain.ainvoke(context)
        
        # Step 5: Create InsightResponse
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
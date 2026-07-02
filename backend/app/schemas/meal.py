from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class MealBase(BaseModel):
    name: str
    price: float
    location: str
    description: Optional[str] = None
    confidence: float = 100.0
    image_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class MealCreate(MealBase):
    pass

class Meal(MealBase):
    id: int

    class Config:
        from_attributes = True


# Day 10: InsightResponse schema for RAG-grounded AI insights
class InsightResponse(BaseModel):
    """Structured AI insight with market context."""
    verdict: Literal["best_deal", "good_value", "fair", "overpriced"] = Field(
        description="Value verdict based on market comparison"
    )
    summary: str = Field(
        description="1-2 sentences grounded in real market data",
        max_length=300
    )
    tip: str = Field(
        description="Actionable advice for the user",
        max_length=200
    )
    price_percentile: int = Field(
        description="Percentile ranking (0-100). 23 means cheaper than 77% of similar meals",
        ge=0,
        le=100
    )
    confidence: int = Field(
        description="AI confidence in this analysis (0-100)",
        ge=0,
        le=100
    )

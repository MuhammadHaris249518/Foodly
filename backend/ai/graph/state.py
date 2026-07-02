from typing import TypedDict, Optional
from pydantic import BaseModel, Field

# This is the structured output we want the LLM to give us
class ExtractedPrice(BaseModel):
    restaurant_name: str = Field(description="Name of the restaurant")
    meal_name: str = Field(description="Name of the food item")
    price_pkr: int = Field(description="The extracted price in PKR. Use 0 if not found.")
    confidence: int = Field(description="Confidence score from 0 to 100 based on the source quality.")
    source_url: Optional[str] = Field(description="URL where the price was found, if available.")

# This is the memory (state) that gets passed through our LangGraph nodes
class AgentState(TypedDict):
    search_query: str             # What the user wants to find
    search_results: str           # The raw text scraped from the web
    extracted_data: Optional[ExtractedPrice] # The final structured output
    iterations: int               # Keep track of loops to prevent infinite scraping
    meal_id: Optional[int]
    thread_id: Optional[str]         # for HITL resume
    validation_passed: Optional[bool]
    retry_reason: Optional[str]
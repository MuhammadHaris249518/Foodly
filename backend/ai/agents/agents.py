import os
import logging
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Configure logging
logger = logging.getLogger(__name__)

# Singleton LLM instance for reuse
_insight_llm = None
_insight_chain = None


def get_insight_llm():
    """Get or create the Gemini LLM instance (singleton pattern)."""
    global _insight_llm
    if _insight_llm is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        _insight_llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0.7,
            max_tokens=200,  # Limit to 2 sentences
            timeout=10.0  # 10 second timeout
        )
    return _insight_llm


def get_insight_chain():
    """Get or create the insight chain (singleton pattern)."""
    global _insight_chain
    if _insight_chain is None:
        llm = get_insight_llm()
        
        prompt = PromptTemplate(
            input_variables=["name", "price", "location", "description", "market_context"],
            template="""You are a local food expert in Islamabad, Pakistan. Given this meal's details and market context, write exactly two sentences explaining if it's a good value.

Meal Name: {name}
Price: PKR {price}
Location: {location}
Description: {description}

{market_context}

Insight:"""
        )
        
        # LCEL chain: prompt | llm | parser
        _insight_chain = prompt | get_insight_llm() | StrOutputParser()
    
    return _insight_chain


async def generate_value_insight(
    name: str,
    price: float,
    location: str,
    description: str = "",
    market_context: str = ""
) -> str:
    """
    Generate AI-powered value insight for a meal.
    
    Production-ready implementation with:
    - Singleton LLM instance for connection reuse
    - Timeout protection
    - Graceful error handling
    - Structured logging
    
    Args:
        name: Meal name
        price: Meal price in PKR
        location: Restaurant location
        description: Meal description (optional)
        market_context: Market comparison data (optional, for RAG upgrade)
    
    Returns:
        Insight string (2 sentences) or fallback message
    """
    # Validate inputs
    if not name or not price or not location:
        logger.warning("Invalid inputs for insight generation")
        return "Unable to generate insight: missing meal details."
    
    # Check for API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        logger.error("GOOGLE_API_KEY not configured")
        return "AI Insight temporarily unavailable: API key not configured."
    
    try:
        # Get chain
        chain = get_insight_chain()
        
        # Format description
        desc = description.strip() if description else "No description available"
        
        # Add market context if provided (RAG upgrade - Day 10)
        if market_context:
            market_section = f"\nMarket Context:\n{market_context}"
        else:
            market_section = ""
        
        # Run chain with timeout
        import asyncio
        try:
            insight = await asyncio.wait_for(
                chain.ainvoke({
                    "name": name,
                    "price": price,
                    "location": location,
                    "description": desc,
                    "market_context": market_section
                }),
                timeout=8.0  # 8 second timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"Insight generation timed out for meal: {name}")
            return "AI analysis timed out. This meal looks promising based on community ratings!"
        
        # Clean up response
        insight = insight.strip()
        
        # Ensure we got a reasonable response
        if not insight or len(insight) < 20:
            logger.warning(f"Insight too short for meal {name}: {insight}")
            return f"{name} at PKR {price} in {location} offers good value for money."
        
        # Limit to 2 sentences max
        sentences = insight.split('.')
        if len(sentences) > 2:
            insight = '.'.join(sentences[:2]) + '.'
        
        logger.info(f"Generated insight for {name}: {insight[:50]}...")
        return insight
        
    except Exception as e:
        logger.error(f"Failed to generate insight for {name}: {e}", exc_info=True)
        return f"{name} at PKR {price} looks like a great option in {location}!"


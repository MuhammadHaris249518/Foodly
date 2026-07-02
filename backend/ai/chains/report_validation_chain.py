import os
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

class ValidationResult(BaseModel):
    is_realistic: bool = Field(description="True if the price is realistic for this meal, False otherwise.")
    reason: str = Field(description="A short explanation of why the price was accepted or rejected.")

def get_validation_chain():
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="llama-3.3-70b-versatile",
        temperature=0.1
    )
    
    structured_llm = llm.with_structured_output(ValidationResult)
    
    prompt = PromptTemplate(
        input_variables=["meal_name", "reported_price", "current_price"],
        template="""You are a Pakistani food pricing expert. 
A user has reported that the price of '{meal_name}' is {reported_price} PKR.
The current known average price is {current_price} PKR.
Determine if this reported price is realistic. Small variations are fine, but absurd numbers (like 50000 PKR for chai, or 5 PKR for biryani) are fake spam.

Respond only with the structured output."""
    )
    
    return prompt | structured_llm

async def validate_price_report(meal_name: str, current_price: float, reported_price: float) -> tuple[bool, str]:
    """
    Returns (is_valid, reason)
    """
    # 1. Statistical fast-path pre-check
    if current_price > 0:
        if reported_price > current_price * 3:
            return False, f"Price {reported_price} PKR is unrealistically high compared to the average of {current_price} PKR."
        if reported_price < current_price / 4:
            return False, f"Price {reported_price} PKR is unrealistically low compared to the average of {current_price} PKR."
            
    # 2. LLM Gatekeeper
    chain = get_validation_chain()
    try:
        result = await chain.ainvoke({"meal_name": meal_name, "reported_price": reported_price, "current_price": current_price})
        return result.is_realistic, result.reason
    except Exception as e:
        print(f"Validation chain failed: {e}")
        # Default to accept if AI fails, so we don't block valid reports
        return True, "AI validation unreachable, assumed valid."

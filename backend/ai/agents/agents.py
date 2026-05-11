import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# Load the environment variables from the .env file in the backend directory
load_dotenv()

def generate_value_insight(name: str, price: float, location: str, description: str = "") -> str:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "AI Insight temporarily unavailable: GOOGLE_API_KEY missing in environment."
        
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=api_key)
        
        prompt = PromptTemplate(
            input_variables=["name", "price", "location", "description"],
            template="""You are a local food expert. Given this meal's details, write exactly two sentences explaining if it's a good value.
            
Meal Name: {name}
Price: {price}
Location: {location}
Description: {description}

Insight:"""
        )
        
        formatted_prompt = prompt.format(name=name, price=price, location=location, description=description or "No description provided")
        response = llm.invoke(formatted_prompt)
        return response.content.strip()
    except Exception as e:
        print(f"Failed to generate insight: {e}")
        return "This looks like a great meal option, but our AI value analysis is currently unreachable."


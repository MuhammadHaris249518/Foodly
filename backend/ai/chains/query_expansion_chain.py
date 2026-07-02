import os
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

def get_expansion_chain():
    llm = ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="llama-3.3-70b-versatile",
        temperature=0.3
    )

    prompt = PromptTemplate(
        input_variables=["query"],
        template="""You are a Pakistani food expert. The user is searching for '{query}'.
List up to 5 specific, popular Pakistani meal names or variations that match this broad query.
Return ONLY a valid JSON array of strings, with no other text, markdown formatting, or explanations.
Example output: ["biryani", "karahi", "nihari", "haleem", "pulao"]
"""
    )
    
    chain = prompt | llm | JsonOutputParser()
    return chain

async def expand_query(query: str) -> list[str]:
    chain = get_expansion_chain()
    try:
        # Expected output is a list of strings
        expanded_terms = await chain.ainvoke({"query": query})
        if isinstance(expanded_terms, list):
            return expanded_terms
        return []
    except Exception as e:
        print(f"Query expansion failed: {e}")
        return []

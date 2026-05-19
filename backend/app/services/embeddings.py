import os
from typing import List, Optional
from google import genai
from google.genai.types import EmbedContentConfig

EMBEDDING_MODEL = "text-embedding-004"
EMBEDDING_DIMENSIONS = 1536

_client: Optional[genai.Client] = None


def _get_client() -> Optional[genai.Client]:
    global _client
    if _client is not None:
        return _client
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return None
    _client = genai.Client(api_key=api_key)
    return _client


def embed_query(text: str) -> Optional[List[float]]:
    client = _get_client()
    if client is None:
        return None
    config = EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSIONS)
    result = client.models.embed_content(model=EMBEDDING_MODEL, contents=text, config=config)
    return list(result.embeddings[0].values)

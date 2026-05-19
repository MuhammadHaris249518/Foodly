import os
import sys
from typing import Iterable
from dotenv import load_dotenv
from google import genai
from google.genai.types import EmbedContentConfig

# Add the app directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import SessionLocal
from app.models.meal import Meal

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY not found in environment variables.")

client = genai.Client(api_key=GOOGLE_API_KEY)

EMBEDDING_DIMENSIONS = 1536
EMBEDDING_MODEL = "text-embedding-004"


def build_context(meal: Meal) -> str:
    parts = [meal.name, meal.location, meal.description or ""]
    return ". ".join(part for part in parts if part)


def embed_text(text: str) -> list[float]:
    config = EmbedContentConfig(output_dimensionality=EMBEDDING_DIMENSIONS)
    result = client.models.embed_content(model=EMBEDDING_MODEL, contents=text, config=config)
    return list(result.embeddings[0].values)


def batched(items: Iterable[Meal], batch_size: int) -> Iterable[list[Meal]]:
    batch: list[Meal] = []
    for item in items:
        batch.append(item)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


def generate_embeddings(batch_size: int = 8, force: bool = False) -> None:
    db = SessionLocal()
    try:
        query = db.query(Meal)
        if not force:
            query = query.filter(Meal.embedding.is_(None))

        meals = query.all()
        print(f"Embedding {len(meals)} meals...")

        for chunk in batched(meals, batch_size):
            for meal in chunk:
                context = build_context(meal)
                try:
                    meal.embedding = embed_text(context)
                except Exception as exc:
                    print(f"Failed to embed {meal.name}: {exc}")
            db.commit()

        print("Embedding update complete.")
    finally:
        db.close()


if __name__ == "__main__":
    generate_embeddings()

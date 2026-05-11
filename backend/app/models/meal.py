from sqlalchemy import Column, Integer, String, Float
from pgvector.sqlalchemy import Vector
from ..core.database import Base

class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    location = Column(String)
    description = Column(String, nullable=True)
    confidence = Column(Float, default=100.0)
    image_url = Column(String, nullable=True)
    # Vector embedding for semantic search (e.g., 1536 dimensions for OpenAI or similar)
    embedding = Column(Vector(1536), nullable=True)




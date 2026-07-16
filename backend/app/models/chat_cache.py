from sqlalchemy import Column, Integer, String, DateTime, func
from pgvector.sqlalchemy import Vector
from ..core.database import Base


class ChatQueryCache(Base):
    """
    Stores embeddings of past /chat queries so a semantically similar
    future query (cosine distance < threshold) can skip the LLM call.
    Sprint 12 foundation — not read from or written to by /chat yet.
    """
    __tablename__ = "chat_query_cache"

    id = Column(Integer, primary_key=True)
    query_text = Column(String, nullable=False)
    embedding = Column(Vector(1536), nullable=False)
    redis_key = Column(String, nullable=False)  # points at the full cached response body in Redis
    created_at = Column(DateTime(timezone=True), server_default=func.now())
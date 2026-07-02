from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from ..core.database import Base


class PendingVerification(Base):
    __tablename__ = "pending_verifications"

    id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(Integer, ForeignKey("meals.id", ondelete="CASCADE"), nullable=False)
    source = Column(String(50), default="community")  # community or web_agent
    raw_data = Column(JSONB, nullable=True)
    extracted_price = Column(Float, nullable=False)
    confidence = Column(Float, default=100.0)
    status = Column(String(20), default="pending")
    agent_thread_id = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Keeping old fields for backwards compatibility with existing code until we fully migrate reports
    reported_price = Column(Float, nullable=True)
    reporter_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes = Column(String(2000), nullable=True)
    reporter_name = Column(String(100), nullable=True)
    photo_url = Column(String, nullable=True)

from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from ..core.database import Base


class PendingVerification(Base):
    __tablename__ = "pending_verifications"

    id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(Integer, ForeignKey("meals.id", ondelete="CASCADE"), nullable=False)
    reported_price = Column(Float, nullable=False)
    notes = Column(String, nullable=True)
    reporter_name = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

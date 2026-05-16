from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ReportCreate(BaseModel):
    meal_id: int
    reported_price: float
    notes: Optional[str] = None
    reporter_name: Optional[str] = None


class Report(BaseModel):
    id: int
    meal_id: int
    reported_price: float
    notes: Optional[str] = None
    reporter_name: Optional[str] = None
    photo_url: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

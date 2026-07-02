from pydantic import BaseModel
from typing import Optional, List
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


class AdminReport(Report):
    meal_name: Optional[str] = None
    meal_price: Optional[float] = None
    meal_location: Optional[str] = None


class AdminStats(BaseModel):
    meals_total: int
    total_users: int
    reports_total: int
    reports_pending: int
    reports_approved: int
    reports_rejected: int
    avg_confidence: float


class AdminMealDetail(BaseModel):
    id: int
    name: str
    price: float
    location: Optional[str] = None
    confidence_score: float
    report_count: int
    last_reported_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class BulkApproveRequest(BaseModel):
    ids: List[int]


class BulkApproveResponse(BaseModel):
    approved: int
    skipped: int

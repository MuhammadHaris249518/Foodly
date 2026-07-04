from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    location: Optional[str] = None


class UserCreate(UserBase):
    # Deliberately no `role` field — role is never client-settable.
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(UserBase):
    id: int
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileOut(BaseModel):
    email: EmailStr
    saved_count: int
    report_count: int
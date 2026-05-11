from pydantic import BaseModel
from typing import Optional, List

class MealBase(BaseModel):
    name: str
    price: float
    location: str
    description: Optional[str] = None
    confidence: float = 100.0
    image_url: Optional[str] = None

class MealCreate(MealBase):
    pass

class Meal(MealBase):
    id: int

    class Config:
        from_attributes = True

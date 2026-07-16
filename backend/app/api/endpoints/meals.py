from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ...core.database import get_db
from ...schemas import meal as meal_schema
from ...services.auth import get_current_user, require_admin
from ...core.rate_limit import limiter
from ...models.user import User
from ...services.meal import meal_service
from ...core.cache import invalidate_pattern

router = APIRouter()

@router.get("", response_model=List[meal_schema.Meal])
@router.get("/", response_model=List[meal_schema.Meal])
@limiter.limit("30/minute")
async def read_meals(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    budget: float | None = None,
    search: str | None = None,
    db: Session = Depends(get_db)
):
    return await meal_service.get_meals(db=db, skip=skip, limit=limit, budget=budget, search=search)

@router.get("/nearby", response_model=List[meal_schema.Meal])
async def read_meals_nearby(
    response: Response,
    lat: float,
    lng: float,
    radius_km: float = 3.0,
    budget: float | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    meals, cache_hit = await meal_service.get_nearby_meals(
        db=db, lat=lat, lng=lng, radius_km=radius_km, budget=budget, search=search
    )
    response.headers["X-Cache"] = "HIT" if cache_hit else "MISS"
    return meals

@router.post("/", response_model=meal_schema.Meal)
async def create_meal(
    meal: meal_schema.MealCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    result = meal_service.create_meal(db=db, meal_data=meal)
    await invalidate_pattern("nearby:*")
    await invalidate_pattern("search_cache:*")
    return result

@router.post("/{meal_id}/save", response_model=meal_schema.Meal)
def save_meal(
    meal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return meal_service.save_meal(db=db, meal_id=meal_id, user_id=current_user.id)

@router.delete("/{meal_id}/save", status_code=204)
def unsave_meal(
    meal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    meal_service.unsave_meal(db=db, meal_id=meal_id, user_id=current_user.id)

@router.get("/{meal_id}", response_model=Dict[str, Any])
async def read_meal_detail(meal_id: int, db: Session = Depends(get_db)):
    return await meal_service.get_meal_detail(db=db, meal_id=meal_id)
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ...core.database import get_db
from ...models.saved_meal import SavedMeal
from ...models.meal import Meal
from ...schemas import meal as meal_schema
from ...schemas.user import UserProfileOut
from ...services.auth import get_current_user
from ...models.user import User
from ...models.pending_verification import PendingVerification

router = APIRouter()


@router.get("/me/saved", response_model=List[meal_schema.Meal])
def read_saved_meals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    meals = (
        db.query(Meal)
        .join(SavedMeal, SavedMeal.meal_id == Meal.id)
        .filter(SavedMeal.user_id == current_user.id)
        .order_by(SavedMeal.created_at.desc())
        .all()
    )
    return meals


@router.get("/me/profile", response_model=UserProfileOut)
def read_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    saved_count = (
        db.query(SavedMeal)
        .filter(SavedMeal.user_id == current_user.id)
        .count()
    )
    report_count = (
        db.query(PendingVerification)
        .filter(PendingVerification.reporter_user_id == current_user.id)
        .count()
    )
    return UserProfileOut(
        email=current_user.email,
        saved_count=saved_count,
        report_count=report_count
    )

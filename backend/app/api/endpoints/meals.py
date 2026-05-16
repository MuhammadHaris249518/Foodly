from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Dict, Any
from datetime import datetime, timedelta
import random
from ...core.database import get_db
from ...models import meal as meal_model
from ...schemas import meal as meal_schema
from ai.agents.agents import generate_value_insight
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

router = APIRouter()

@router.get("", response_model=List[meal_schema.Meal])
@router.get("/", response_model=List[meal_schema.Meal])
def read_meals(
    skip: int = 0, 
    limit: int = 100, 
    budget: float | None = None,
    search: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(meal_model.Meal)
    
    if budget is not None:
        query = query.filter(meal_model.Meal.price <= budget)
        
    if search:
        search_fmt = f"%{search}%"
        query = query.filter(
            or_(
                meal_model.Meal.name.ilike(search_fmt),
                meal_model.Meal.location.ilike(search_fmt)
            )
        )
        
    meals = query.offset(skip).limit(limit).all()
    return meals

@router.post("/", response_model=meal_schema.Meal)
def create_meal(meal: meal_schema.MealCreate, db: Session = Depends(get_db)):
    db_meal = meal_model.Meal(**meal.dict())
    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    return db_meal

@router.get("/{meal_id}", response_model=Dict[str, Any])
def read_meal_detail(meal_id: int, db: Session = Depends(get_db)):
    meal = db.query(meal_model.Meal).filter(meal_model.Meal.id == meal_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    
    # Simulate price history for the last 6 months
    base_price = meal.price
    price_history = []
    
    for i in range(6, -1, -1):
        month_date = datetime.now() - timedelta(days=30 * i)
        # Random fluctuation between -15% and +15%
        fluctuation = random.uniform(-0.15, 0.15)
        simulated_price = round(base_price * (1 + fluctuation))
        price_history.append({
            "month": month_date.strftime("%b %Y"),
            "price": simulated_price if i != 0 else base_price # Ensure current month is exact price
        })
        
    # Run AI insight generation with a short timeout so page render isn't blocked by slow external APIs
    try:
        ex = ThreadPoolExecutor(max_workers=1)
        future = ex.submit(
            generate_value_insight,
            name=meal.name,
            price=meal.price,
            location=meal.location,
            description=meal.description or ""
        )
        try:
            ai_insight = future.result(timeout=1.5)
        except FuturesTimeoutError:
            try:
                future.cancel()
            except Exception:
                pass
            ai_insight = "AI analysis temporarily unavailable (timed out)."
        except Exception:
            ai_insight = "This looks like a great meal option, but our AI value analysis is currently unreachable."
        finally:
            # Do not wait for the worker thread to finish — shutdown without waiting
            try:
                ex.shutdown(wait=False)
            except Exception:
                pass
    except Exception:
        ai_insight = "This looks like a great meal option, but our AI value analysis is currently unreachable."
    
    return {
        "meal": {
            "id": meal.id,
            "name": meal.name,
            "price": meal.price,
            "location": meal.location,
            "confidence": meal.confidence,
            "image_url": meal.image_url,
            "description": meal.description
        },
        "price_history": price_history,
        "ai_insight": ai_insight
    }

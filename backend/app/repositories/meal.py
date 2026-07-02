from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from ..models import meal as meal_model
from ..models.saved_meal import SavedMeal
from ..models.pending_verification import PendingVerification
from ..schemas import meal as meal_schema

class MealRepository:
    def get_by_id(self, db: Session, meal_id: int) -> Optional[meal_model.Meal]:
        return db.query(meal_model.Meal).filter(meal_model.Meal.id == meal_id).first()

    def list_paginated(
        self, db: Session, skip: int = 0, limit: int = 100, budget: float = None, 
        query_embedding=None, search_fmt: str = None
    ) -> List[meal_model.Meal]:
        query = db.query(meal_model.Meal)
        
        if budget is not None:
            query = query.filter(meal_model.Meal.price <= budget)
            
        if query_embedding is not None:
            query = query.filter(meal_model.Meal.embedding.isnot(None))
            query = query.order_by(meal_model.Meal.embedding.op("<=>")(query_embedding))
        elif search_fmt:
            query = query.filter(
                or_(
                    meal_model.Meal.name.ilike(search_fmt),
                    meal_model.Meal.location.ilike(search_fmt)
                )
            )
            
        return query.offset(skip).limit(limit).all()

    def vector_union_search(
        self, db: Session, embeddings: List[List[float]], limit: int = 20, budget: float = None
    ) -> List[meal_model.Meal]:
        if not embeddings:
            return []
            
        queries = []
        for emb in embeddings:
            q = db.query(meal_model.Meal).filter(meal_model.Meal.embedding.isnot(None))
            if budget is not None:
                q = q.filter(meal_model.Meal.price <= budget)
            q = q.order_by(meal_model.Meal.embedding.op("<=>")(emb)).limit(limit)
            queries.append(q)
            
        if len(queries) == 1:
            return queries[0].all()
            
        from sqlalchemy import union_all
        from sqlalchemy.orm import aliased
        
        union_q = union_all(*[q.subquery() for q in queries])
        MealAlias = aliased(meal_model.Meal, union_q)
        rows = db.query(MealAlias).all()
        
        seen = set()
        unique_meals = []
        for m in rows:
            if m.id not in seen:
                seen.add(m.id)
                unique_meals.append(m)
                
        # Typically reranked by Foodly score afterwards, but we return deduplicated list here
        return unique_meals[:limit]

    def list_nearby(
        self, db: Session, lat: float, lng: float, radius_km: float = 3.0,
        budget: float = None, search_fmt: str = None, limit: int = 50
    ) -> List[meal_model.Meal]:
        query = db.query(meal_model.Meal)
        
        if budget is not None:
            query = query.filter(meal_model.Meal.price <= budget)
            
        if search_fmt:
            query = query.filter(
                or_(
                    meal_model.Meal.name.ilike(search_fmt),
                    meal_model.Meal.location.ilike(search_fmt)
                )
            )
            
        query = query.filter(
            meal_model.Meal.latitude.isnot(None),
            meal_model.Meal.longitude.isnot(None)
        )
        
        user_point = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
        meal_point = func.ST_SetSRID(
            func.ST_MakePoint(meal_model.Meal.longitude, meal_model.Meal.latitude),
            4326
        )
        distance_m = func.ST_DistanceSphere(meal_point, user_point)
        
        query = query.filter(distance_m <= radius_km * 1000.0)
        query = query.order_by(distance_m.asc())
        
        return query.limit(limit).all()

    def create(self, db: Session, meal_data: meal_schema.MealCreate) -> meal_model.Meal:
        db_meal = meal_model.Meal(**meal_data.model_dump())
        db.add(db_meal)
        db.commit()
        db.refresh(db_meal)
        return db_meal
        
    def save_for_user(self, db: Session, meal_id: int, user_id: int) -> bool:
        existing = db.query(SavedMeal).filter(
            SavedMeal.user_id == user_id, 
            SavedMeal.meal_id == meal_id
        ).first()
        if not existing:
            db.add(SavedMeal(user_id=user_id, meal_id=meal_id))
            db.commit()
            return True
        return False
        
    def unsave_for_user(self, db: Session, meal_id: int, user_id: int) -> bool:
        existing = db.query(SavedMeal).filter(
            SavedMeal.user_id == user_id, 
            SavedMeal.meal_id == meal_id
        ).first()
        if existing:
            db.delete(existing)
            db.commit()
            return True
        return False

    def get_approved_reports(self, db: Session, meal_id: int) -> List[PendingVerification]:
        return db.query(PendingVerification).filter(
            PendingVerification.meal_id == meal_id,
            PendingVerification.status == "approved"
        ).order_by(PendingVerification.created_at.asc()).all()

meal_repository = MealRepository()

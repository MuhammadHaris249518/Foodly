from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from ...core.database import get_db
from ...models.pending_verification import PendingVerification
from ...models.user import User
from ...models import meal as meal_model
from ...schemas import report as report_schema
from ...services.auth import require_admin

router = APIRouter()


def _recompute_confidence(db: Session, meal_id: int) -> None:
    pending_count = db.query(PendingVerification).filter(
        PendingVerification.meal_id == meal_id,
        PendingVerification.status == "pending",
    ).count()
    meal = db.query(meal_model.Meal).filter(meal_model.Meal.id == meal_id).first()
    if meal:
        meal.confidence = max(0.0, 100.0 - pending_count * 5.0)
        db.add(meal)
        db.commit()


@router.get("/stats", response_model=report_schema.AdminStats)
def get_admin_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    meals_total = db.query(meal_model.Meal).count()
    total_users = db.query(User).count()
    reports_total = db.query(PendingVerification).count()
    reports_pending = db.query(PendingVerification).filter(PendingVerification.status == "pending").count()
    reports_approved = db.query(PendingVerification).filter(PendingVerification.status == "approved").count()
    reports_rejected = db.query(PendingVerification).filter(PendingVerification.status == "rejected").count()
    avg_confidence_row = db.query(func.avg(meal_model.Meal.confidence)).scalar()
    avg_confidence = round(float(avg_confidence_row), 2) if avg_confidence_row is not None else 0.0
    return report_schema.AdminStats(
        meals_total=meals_total,
        total_users=total_users,
        reports_total=reports_total,
        reports_pending=reports_pending,
        reports_approved=reports_approved,
        reports_rejected=reports_rejected,
        avg_confidence=avg_confidence,
    )


@router.get("/meals", response_model=List[report_schema.AdminMealDetail])
def list_admin_meals(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    rows = (
        db.query(
            meal_model.Meal,
            func.count(PendingVerification.id).label("report_count"),
            func.max(PendingVerification.created_at).label("last_reported_at"),
        )
        .outerjoin(PendingVerification, PendingVerification.meal_id == meal_model.Meal.id)
        .group_by(meal_model.Meal.id)
        .order_by(func.count(PendingVerification.id).desc())
        .all()
    )
    return [
        report_schema.AdminMealDetail(
            id=meal.id,
            name=meal.name,
            price=meal.price,
            location=meal.location,
            confidence_score=meal.confidence,
            report_count=report_count,
            last_reported_at=last_reported_at,
        )
        for meal, report_count, last_reported_at in rows
    ]


@router.post("/reports/bulk-approve", response_model=report_schema.BulkApproveResponse)
def bulk_approve_reports(
    body: report_schema.BulkApproveRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    reports = (
        db.query(PendingVerification)
        .filter(
            PendingVerification.id.in_(body.ids),
            PendingVerification.status == "pending",
        )
        .all()
    )
    approved = 0
    skipped = len(body.ids) - len(reports)
    meal_ids_to_update = set()
    needed_meal_ids = [r.meal_id for r in reports]
    meals_map = {
        m.id: m
        for m in db.query(meal_model.Meal).filter(meal_model.Meal.id.in_(needed_meal_ids)).all()
    }
    for report in reports:
        meal = meals_map.get(report.meal_id)
        if meal:
            meal.price = report.reported_price
            db.add(meal)
        report.status = "approved"
        db.add(report)
        meal_ids_to_update.add(report.meal_id)
        approved += 1
    db.commit()
    for meal_id in meal_ids_to_update:
        _recompute_confidence(db, meal_id)
    return report_schema.BulkApproveResponse(approved=approved, skipped=skipped)


@router.get("/reports", response_model=List[report_schema.AdminReport])
def list_reports(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    query = db.query(PendingVerification, meal_model.Meal).join(
        meal_model.Meal, PendingVerification.meal_id == meal_model.Meal.id
    )
    if status:
        query = query.filter(PendingVerification.status == status)

    rows = query.order_by(PendingVerification.created_at.desc()).limit(200).all()
    results: List[report_schema.AdminReport] = []
    for report, meal in rows:
        results.append(
            report_schema.AdminReport(
                id=report.id,
                meal_id=report.meal_id,
                reported_price=report.reported_price,
                notes=report.notes,
                reporter_name=report.reporter_name,
                photo_url=report.photo_url,
                status=report.status,
                created_at=report.created_at,
                meal_name=meal.name if meal else None,
                meal_price=meal.price if meal else None,
                meal_location=meal.location if meal else None,
            )
        )
    return results


@router.post("/reports/{report_id}/approve", response_model=report_schema.Report)
def approve_report(
    report_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    report = db.query(PendingVerification).filter(PendingVerification.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != "pending":
        raise HTTPException(status_code=400, detail="Report already processed")

    meal = db.query(meal_model.Meal).filter(meal_model.Meal.id == report.meal_id).first()
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")

    meal.price = report.reported_price
    report.status = "approved"
    db.add(meal)
    db.add(report)
    db.commit()
    db.refresh(report)

    _recompute_confidence(db, report.meal_id)

    return report


@router.post("/reports/{report_id}/reject", response_model=report_schema.Report)
def reject_report(
    report_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    report = db.query(PendingVerification).filter(PendingVerification.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.status != "pending":
        raise HTTPException(status_code=400, detail="Report already processed")

    report.status = "rejected"
    db.add(report)
    db.commit()
    db.refresh(report)

    _recompute_confidence(db, report.meal_id)

    return report
import os
import uuid
import traceback
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from ...core.database import get_db
from ...core.config import settings
import requests
from ...models.pending_verification import PendingVerification
from ...models import meal as meal_model
from ...models.user import User
from ...schemas import report as report_schema
from ...services.auth import get_current_user_optional

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads", "reports")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("", response_model=report_schema.Report, status_code=201)
async def create_report(
    meal_id: int = Form(...),
    reported_price: float = Form(...),
    notes: Optional[str] = Form(None),
    reporter_name: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    try:
        if reported_price < 0:
            raise HTTPException(status_code=400, detail="reported_price must be non-negative")

        meal = db.query(meal_model.Meal).filter(meal_model.Meal.id == meal_id).first()
        if not meal:
            raise HTTPException(status_code=404, detail="Meal not found")

        # -----------------------------
        # AI Report Validator Integration
        # -----------------------------
        from ai.chains.report_validation_chain import validate_price_report
        is_valid, reason = await validate_price_report(meal.name, meal.price, reported_price)
        if not is_valid:
            raise HTTPException(status_code=422, detail=f"Report rejected by AI Gatekeeper: {reason}")
        # -----------------------------

        photo_url = None
        if photo:
            if photo.content_type not in ("image/jpeg", "image/png", "image/webp"):
                raise HTTPException(status_code=400, detail="Unsupported image type")
            contents = photo.file.read()
            if len(contents) > 5 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Photo too large")
            # os.path.basename strips any path traversal from the original filename
            safe_name = os.path.basename(photo.filename or "upload")
            filename = f"{uuid.uuid4().hex}_{safe_name}"
            save_path = os.path.join(UPLOAD_DIR, filename)
            with open(save_path, "wb") as f:
                f.write(contents)
            # Use forward slash explicitly — os.path.join uses backslash on Windows
            photo_url = f"/uploads/reports/{filename}"

        new_report = PendingVerification(
            meal_id=meal_id,
            reporter_user_id=current_user.id if current_user else None,
            reported_price=reported_price,
            notes=notes,
            reporter_name=reporter_name,
            photo_url=photo_url,
            status="pending",
        )
        db.add(new_report)
        db.commit()
        db.refresh(new_report)

        pending_count = db.query(PendingVerification).filter(
            PendingVerification.meal_id == meal_id,
            PendingVerification.status == "pending"
        ).count()
        meal.confidence = max(0.0, 100.0 - pending_count * 5.0)
        db.add(meal)
        db.commit()

        def _notify_n8n(report_id: int):
            webhook = settings.N8N_WEBHOOK_URL
            if not webhook:
                return
            try:
                payload = {
                    "report_id": report_id,
                    "meal_id": meal_id,
                    "reported_price": reported_price,
                    "status": new_report.status,
                }
                requests.post(webhook, json=payload, timeout=5)
            except Exception as e:
                try:
                    log_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs")
                    os.makedirs(log_path, exist_ok=True)
                    with open(os.path.join(log_path, "n8n_notifications.log"), "a", encoding="utf-8") as lf:
                        lf.write(f"Failed to send n8n notification: {e}\n")
                except Exception:
                    pass

        if background_tasks is not None:
            background_tasks.add_task(_notify_n8n, new_report.id)

        return new_report
    except HTTPException:
        raise
    except Exception:
        tb = traceback.format_exc()
        log_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs")
        try:
            os.makedirs(log_path, exist_ok=True)
            with open(os.path.join(log_path, "reports_error.log"), "a", encoding="utf-8") as lf:
                lf.write(tb + "\n\n")
        except Exception:
            pass
        raise HTTPException(status_code=500, detail="Internal Server Error")

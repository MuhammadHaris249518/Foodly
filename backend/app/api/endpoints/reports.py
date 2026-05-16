import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from ...core.database import get_db
from ...core.config import settings
import requests
from ...models.pending_verification import PendingVerification
from ...models import meal as meal_model
from ...schemas import report as report_schema

router = APIRouter()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "uploads", "reports")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("", response_model=report_schema.Report, status_code=201)
def create_report(
    meal_id: int = Form(...),
    reported_price: float = Form(...),
    notes: Optional[str] = Form(None),
    reporter_name: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    import traceback
    try:
        meal = db.query(meal_model.Meal).filter(meal_model.Meal.id == meal_id).first()
        if not meal:
            raise HTTPException(status_code=404, detail="Meal not found")

        photo_url = None
        if photo:
            # basic validation
            if photo.content_type not in ("image/jpeg", "image/png", "image/webp"):
                raise HTTPException(status_code=400, detail="Unsupported image type")
            contents = photo.file.read()
            if len(contents) > 5 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Photo too large")
            filename = f"{uuid.uuid4().hex}_{photo.filename}"
            save_path = os.path.join(UPLOAD_DIR, filename)
            with open(save_path, "wb") as f:
                f.write(contents)
            # store relative path
            photo_url = os.path.join("/uploads/reports", filename)

        new_report = PendingVerification(
            meal_id=meal_id,
            reported_price=reported_price,
            notes=notes,
            reporter_name=reporter_name,
            photo_url=photo_url,
            status="pending",
        )
        db.add(new_report)
        db.commit()
        db.refresh(new_report)

        # Recompute confidence: simple rule -> 100 - pending_count*5
        pending_count = db.query(PendingVerification).filter(
            PendingVerification.meal_id == meal_id,
            PendingVerification.status == "pending"
        ).count()
        meal.confidence = max(0.0, 100.0 - pending_count * 5.0)
        db.add(meal)
        db.commit()
        # Trigger n8n webhook asynchronously if configured
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
                # best-effort logging
                try:
                    log_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs")
                    os.makedirs(log_path, exist_ok=True)
                    with open(os.path.join(log_path, "n8n_notifications.log"), "a", encoding="utf-8") as lf:
                        lf.write(f"Failed to send n8n notification: {e}\n")
                except Exception:
                    print("Failed to log n8n notification error")

        try:
            if background_tasks is not None:
                background_tasks.add_task(_notify_n8n, new_report.id)
            else:
                # fallback: fire-and-forget
                try:
                    _notify_n8n(new_report.id)
                except Exception:
                    pass
        except Exception:
            pass

        return new_report
    except HTTPException:
        # Re-raise HTTPExceptions unchanged
        raise
    except Exception as e:
        tb = traceback.format_exc()
        # write traceback to a log file for debugging
        log_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "logs")
        try:
            os.makedirs(log_path, exist_ok=True)
            with open(os.path.join(log_path, "reports_error.log"), "a", encoding="utf-8") as lf:
                lf.write(tb + "\n\n")
        except Exception:
            # best-effort logging
            print("Failed to write error log")
        print(tb)
        raise HTTPException(status_code=500, detail="Internal Server Error")

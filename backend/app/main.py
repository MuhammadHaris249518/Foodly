from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from .core.config import settings
from .core.database import get_db
from .api.endpoints import meals, reports, auth, users, admin, agent

app = FastAPI(title=settings.PROJECT_NAME)

# ── CORS: env-driven origin whitelist ───────────────────────────────────
# CHANGED: previously allow_origins=["*"] combined with allow_credentials=True.
# That combination is unsafe: Starlette can't literally send "*" alongside
# credentials (disallowed by the CORS spec), so it falls back to reflecting
# whatever Origin header the request sent — meaning ANY website could make
# credentialed requests (with the user's JWT/cookies attached) and read the
# response. Fixed by supplying a real closed list of trusted origins from
# settings.cors_origins (env-driven — see core/config.py). Credentials are
# now only ever echoed back for an origin on this explicit list.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(meals.router, prefix="/api/v1/meals", tags=["meals"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(agent.router, prefix="/api/v1/agent", tags=["agent"])

# Serve uploaded files during development
import os
uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
uploads_dir = os.path.abspath(uploads_dir)
if os.path.isdir(uploads_dir):
    app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

@app.get("/")
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception:
        return JSONResponse(status_code=503, content={"status": "error", "database": "unavailable"})
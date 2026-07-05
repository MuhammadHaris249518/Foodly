from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
from slowapi import _rate_limit_exceeded_handler  # CHANGED
from slowapi.errors import RateLimitExceeded  # CHANGED
from slowapi.middleware import SlowAPIMiddleware  # CHANGED
from .core.config import settings
from .core.database import get_db
from .core.rate_limit import limiter  # CHANGED
from .core.security_headers import SecurityHeadersMiddleware  # CHANGED
from .core.logging_config import configure_logging, RequestLoggingMiddleware  # CHANGED
from .api.endpoints import meals, reports, auth, users, admin, agent,chat

configure_logging()  # CHANGED: structlog setup, must run before any logger.info() calls

app = FastAPI(title=settings.PROJECT_NAME)

# CHANGED: rate limiting — see core/rate_limit.py for key strategy (user > IP)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS — env-driven whitelist (see previous fix); unchanged in this sprint
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CHANGED: security headers on every response
app.add_middleware(SecurityHeadersMiddleware)

# CHANGED: structured request logging (foundation — full print() removal is Sprint 13/26)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(meals.router, prefix="/api/v1/meals", tags=["meals"])
app.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(agent.router, prefix="/api/v1/agent", tags=["agent"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])  # CHANGED: new in Sprint 3

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
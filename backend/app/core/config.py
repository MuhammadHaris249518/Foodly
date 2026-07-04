from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Foodly"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/foodly_db")
    N8N_WEBHOOK_URL: str | None = os.getenv("N8N_WEBHOOK_URL")
    # ADMIN_SECRET removed — replaced by role-based JWT auth (see services/auth.require_admin)
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # ── CORS: env-driven origin whitelist (replaces wildcard "*") ──────────
    # Comma-separated list, e.g.:
    #   ALLOWED_ORIGINS=http://localhost:3000,https://foodly.pk,https://www.foodly.pk
    # Falls back to common localhost dev ports if unset, so local dev keeps
    # working without extra setup — but production MUST set this explicitly.
    ALLOWED_ORIGINS: str = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000"
    )

    @property
    def cors_origins(self) -> list[str]:
        """Parsed, whitespace-trimmed, empty-entry-free list of allowed origins."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    class Config:
        case_sensitive = True

settings = Settings()
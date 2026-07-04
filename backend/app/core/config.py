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

    class Config:
        case_sensitive = True

settings = Settings()
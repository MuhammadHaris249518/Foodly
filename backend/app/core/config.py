from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Foodly"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/foodly_db")
    N8N_WEBHOOK_URL: str | None = os.getenv("N8N_WEBHOOK_URL")

    class Config:
        case_sensitive = True

settings = Settings()

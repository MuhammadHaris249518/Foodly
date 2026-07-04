from pydantic_settings import BaseSettings
from pydantic import model_validator
from dotenv import load_dotenv
import os

load_dotenv()

# CHANGED: values that must never have an insecure fallback. Any env var
# whose value matches one of these (case-insensitive) is treated as if it
# were never set at all — this catches the case where someone "fixes" the
# missing-var error by literally typing SECRET_KEY=change-me into .env.
_INSECURE_PLACEHOLDER_VALUES = {
    "change-me", "changeme", "secret", "password", "123456",
    "your-secret-key-here", "your-minimum-32-character-secret-key-here",
    "",
}

_MIN_SECRET_KEY_LENGTH = 32  # bytes — matches README's documented requirement


class Settings(BaseSettings):
    PROJECT_NAME: str = "Foodly"

    # CHANGED: no default. Previously:
    #   DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/foodly_db")
    # That default embeds a real-looking credential and would let the app
    # boot against a guessable local DB URL if the env var is ever missing
    # in a new environment (e.g. a fresh container). Now required — missing
    # this var fails startup immediately via Pydantic's ValidationError.
    DATABASE_URL: str

    N8N_WEBHOOK_URL: str | None = os.getenv("N8N_WEBHOOK_URL")

    # ADMIN_SECRET removed — replaced by role-based JWT auth (see services/auth.require_admin)

    # CHANGED: no default. Previously:
    #   SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me")
    # "change-me" is a real, public (checked into git) value — any JWT
    # issued while this default is active can be forged by anyone who
    # knows the string. Now required; see model_validator below for the
    # additional length/placeholder checks.
    SECRET_KEY: str

    # Not secrets — safe to keep sane defaults for deployment convenience.
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # CORS whitelist (see previous CORS fix) — not a secret, dev-friendly default is fine.
    ALLOWED_ORIGINS: str = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000"
    )

    @property
    def cors_origins(self) -> list[str]:
        """Parsed, whitespace-trimmed, empty-entry-free list of allowed origins."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

    # CHANGED: new validator. Pydantic's required-field check alone only
    # verifies SECRET_KEY/DATABASE_URL are *present* — it can't know that
    # "change-me" or a 4-character string are insecure values someone typed
    # in anyway. This closes that gap with an explicit, loud failure.
    @model_validator(mode="after")
    def _validate_secrets(self) -> "Settings":
        if self.SECRET_KEY.strip().lower() in _INSECURE_PLACEHOLDER_VALUES:
            raise RuntimeError(
                "SECRET_KEY is missing or set to an insecure placeholder value. "
                "Generate a real secret (e.g. `openssl rand -hex 32`) and set it "
                "via the SECRET_KEY environment variable before starting the app."
            )
        if len(self.SECRET_KEY.encode("utf-8")) < _MIN_SECRET_KEY_LENGTH:
            raise RuntimeError(
                f"SECRET_KEY must be at least {_MIN_SECRET_KEY_LENGTH} bytes long "
                f"(got {len(self.SECRET_KEY.encode('utf-8'))}). "
                "Generate one with `openssl rand -hex 32`."
            )
        if self.DATABASE_URL.strip().lower() in _INSECURE_PLACEHOLDER_VALUES:
            raise RuntimeError(
                "DATABASE_URL is missing or empty. Set it via the DATABASE_URL "
                "environment variable before starting the app."
            )
        return self

    class Config:
        case_sensitive = True

settings = Settings()
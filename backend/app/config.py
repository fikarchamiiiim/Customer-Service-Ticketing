from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BACKEND_DIR.parent


class Settings(BaseSettings):
    """Konfigurasi aplikasi. Sumber: backend/.env, lalu .env di root repo, lalu env var."""

    model_config = SettingsConfigDict(
        env_file=(str(ROOT_DIR / ".env"), str(BACKEND_DIR / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "CS Ticketing API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql+asyncpg://ticketing:ticketing@localhost:5432/ticketing"

    jwt_secret: str = "dev-secret"
    session_cookie_name: str = "session"
    cookie_secure: bool = False
    google_client_id: str = ""
    agent_emails: str = ""
    dev_auth: bool = True

    allowed_origins: str = "http://localhost:5173"

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def agent_email_set(self) -> set[str]:
        return {e.strip().lower() for e in self.agent_emails.split(",") if e.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

"""
Application configuration.

Loads settings from environment variables / .env file using pydantic-settings.
No secrets are hardcoded here - everything is sourced from the environment so
the same codebase works across dev, test, and production without code changes.
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "MediFlow AI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    SECRET_KEY: str = "insecure-dev-key-change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"

    DATABASE_URL: str = "postgresql+psycopg2://mediflow:mediflow_password@localhost:5432/mediflow"

    POSTGRES_USER: str = "mediflow"
    POSTGRES_PASSWORD: str = "mediflow_password"
    POSTGRES_DB: str = "mediflow"

    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    SEED_ADMIN_EMAIL: str = "admin@mediflow.ai"
    SEED_ADMIN_PASSWORD: str = "Admin@12345"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance so we don't re-parse env vars on every call."""
    return Settings()


settings = get_settings()

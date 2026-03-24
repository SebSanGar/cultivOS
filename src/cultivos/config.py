"""
Kitchen Intelligence configuration — Pydantic settings from .env file.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All settings from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    db_url: str = "sqlite:///cultivos.db"

    # Auth
    jwt_secret_key: str = "change-me-in-production-use-a-random-32-char-string"
    jwt_expiry_minutes: int = 480  # 8-hour kitchen shift

    # Server
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:8000"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

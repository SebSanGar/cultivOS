"""
cultivOS configuration — Pydantic settings from .env file.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All settings from environment variables / .env file."""

    # Database
    db_url: str = "sqlite:///cultivos.db"

    # Auth
    jwt_secret_key: str = ""  # MUST be set via JWT_SECRET_KEY env var in production
    auth_enabled: bool = False  # Set True in production

    # WhatsApp
    whatsapp_api_token: str | None = None
    whatsapp_phone_id: str | None = None

    # Weather
    openweather_api_key: str | None = None

    # S3 storage
    s3_bucket: str = "cultivos-imagery"
    s3_endpoint: str | None = None

    # Optional
    anthropic_api_key: str | None = None
    redis_url: str | None = None

    # Server
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

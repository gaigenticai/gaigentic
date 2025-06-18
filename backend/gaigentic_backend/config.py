"""Application settings loader using pydantic."""
from __future__ import annotations

import logging
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    database_url: str = Field(..., alias="DATABASE_URL")
    superagent_url: str | None = Field(None, alias="SUPERAGENT_URL")
    app_env: str = Field("local", alias="APP_ENV")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


try:
    settings = Settings()
except ValidationError as exc:  # pragma: no cover - executed on startup
    logger.error("Configuration error: %s", exc)
    raise RuntimeError("DATABASE_URL must be set") from exc

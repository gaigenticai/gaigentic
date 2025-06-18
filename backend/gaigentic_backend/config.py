"""Application settings loader using pydantic."""

from __future__ import annotations

import logging
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


SUPERAGENT_API_KEY_PREFIX = "tenant_"


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    database_url: str = Field(..., alias="DATABASE_URL")
    superagent_url: str = Field(..., alias="SUPERAGENT_URL")
    app_env: str = Field("local", alias="APP_ENV")
    openai_api_key: str | None = Field(None, alias="OPENAI_API_KEY")
    llm_provider: str = Field("openai", alias="LLM_PROVIDER")
    llm_model: str = Field("gpt-3.5-turbo", alias="LLM_MODEL")
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


try:
    settings = Settings()
except ValidationError as exc:  # pragma: no cover - executed on startup
    logger.error("Configuration error: %s", exc)
    raise RuntimeError("DATABASE_URL must be set") from exc

"""Application settings loader using pydantic."""

from __future__ import annotations

import logging
import os
from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


SUPERAGENT_API_KEY_PREFIX = "tenant_"

APP_ENV = os.getenv("APP_ENV", "development")


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    database_url: str = Field(..., alias="DATABASE_URL")
    superagent_url: str = Field(..., alias="SUPERAGENT_URL")
    app_env: str = Field(APP_ENV, alias="APP_ENV")
    llm_providers_enabled: list[str] = Field(["openai"], alias="LLM_PROVIDERS_ENABLED")
    openai_api_key: str | None = Field(None, alias="OPENAI_API_KEY")
    claude_api_key: str | None = Field(None, alias="CLAUDE_API_KEY")
    mistral_api_key: str | None = Field(None, alias="MISTRAL_API_KEY")
    ollama_base_url: str | None = Field(None, alias="OLLAMA_BASE_URL")
    llm_provider: str = Field("openai", alias="LLM_PROVIDER")
    llm_model: str = Field("gpt-3.5-turbo", alias="LLM_MODEL")
    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    cors_origins: str = Field("*", alias="CORS_ORIGINS")
    rate_limit_per_minute: int = Field(60, alias="RATE_LIMIT_PER_MINUTE")
    log_file: str | None = Field(None, alias="LOG_FILE")
    memory_chat_k_default: int = Field(10, alias="MEMORY_CHAT_K_DEFAULT")
    memory_semantic_k_default: int = Field(5, alias="MEMORY_SEMANTIC_K_DEFAULT")

    @field_validator("llm_providers_enabled", mode="before")
    @classmethod
    def _split_providers(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [p.strip() for p in v.split(",") if p.strip()]
        return v

    model_config = SettingsConfigDict(env_file=f".env.{APP_ENV}", env_file_encoding="utf-8")


try:
    settings = Settings()
except ValidationError as exc:  # pragma: no cover - executed on startup
    logger.error("Configuration error: %s", exc)
    raise RuntimeError("DATABASE_URL must be set") from exc

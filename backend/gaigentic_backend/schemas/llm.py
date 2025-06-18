from __future__ import annotations

"""Schemas and enums for LLM configuration."""

import enum
from typing import Optional

from pydantic import BaseModel, Field


class LLMProvider(str, enum.Enum):
    """Supported LLM providers."""

    openai = "openai"
    anthropic = "anthropic"
    mistral = "mistral"
    ollama = "ollama"


class LLMModelConfig(BaseModel):
    """Configuration for selecting an LLM model."""

    provider: LLMProvider = Field(..., description="LLM provider")
    model: str = Field(..., description="Model identifier")
    temperature: float = Field(0.2, ge=0, le=1)
    max_tokens: Optional[int] = Field(default=None, ge=1)


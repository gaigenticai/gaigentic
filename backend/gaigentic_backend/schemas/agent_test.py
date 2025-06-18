"""Pydantic schemas for agent tests."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AgentTestCreate(BaseModel):
    """Schema for creating an agent test."""

    name: str = Field(..., max_length=255)
    input_context: dict
    expected_output: dict


class AgentTestOut(BaseModel):
    """Public representation of an agent test."""

    id: UUID
    name: str
    input_context: dict
    expected_output: dict
    created_at: datetime

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}


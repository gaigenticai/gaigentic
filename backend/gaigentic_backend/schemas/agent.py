"""Pydantic models for Agent API."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AgentCreate(BaseModel):
    """Schema for creating an Agent."""

    name: str = Field(..., description="Name of the agent")
    config: dict = Field(..., description="Agent configuration")


class AgentOut(BaseModel):
    """Schema returned from Agent API."""

    id: UUID
    name: str
    config: dict
    created_at: datetime

    model_config = {
        "json_encoders": {datetime: lambda v: v.isoformat()},
    }

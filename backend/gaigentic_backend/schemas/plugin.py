from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PluginCreate(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    code: str


class PluginOut(BaseModel):
    id: UUID
    name: str
    description: str | None = None
    is_active: bool
    created_at: datetime

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}

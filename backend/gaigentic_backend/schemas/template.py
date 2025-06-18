"""Pydantic schemas for Template API."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from .chat import WorkflowDraft


class TemplateCreate(BaseModel):
    """Schema for creating templates."""

    name: str = Field(..., max_length=255)
    description: str
    workflow_draft: WorkflowDraft
    system_prompt: str | None = None


class TemplateOut(BaseModel):
    """Public representation of a template."""

    id: UUID
    name: str
    description: str
    workflow_draft: WorkflowDraft
    system_prompt: str | None = None
    created_by: str
    created_at: datetime

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}

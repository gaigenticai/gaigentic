"""Schemas for chat interactions."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, validator


class Position(BaseModel):
    """Node position on canvas."""

    x: int
    y: int


class Node(BaseModel):
    """Workflow node."""

    id: str
    type: str
    label: str
    data: dict = Field(default_factory=dict)
    position: Position
    condition: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Python expression controlling execution",
    )
    agent_id: Optional[UUID] = Field(
        default=None,
        description="Override agent ID for this step",
    )


class Edge(BaseModel):
    """Workflow edge connecting two nodes."""

    id: str
    source: str
    target: str
    condition: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Expression controlling edge traversal",
    )


class WorkflowDraft(BaseModel):
    """Workflow draft representation for ReactFlow."""

    nodes: List[Node]
    edges: List[Edge]


class ChatMessage(BaseModel):
    """Single message in a chat session."""

    role: Literal["user", "assistant"]
    content: str
    timestamp: str = Field(..., description="UTC ISO timestamp")

    @validator("timestamp")
    def validate_timestamp(cls, value: str) -> str:  # noqa: D401
        """Ensure timestamp is valid ISO format."""
        try:
            datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("timestamp must be ISO formatted") from exc
        return value


class ChatRequest(BaseModel):
    """Chat request payload."""

    messages: List[ChatMessage]


class ChatResponse(BaseModel):
    """Response returned from the chat endpoint."""

    reply: str
    workflow_draft: Optional[WorkflowDraft] = None


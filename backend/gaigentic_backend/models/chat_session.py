"""Chat session model."""
from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB

from ..database import Base


class ChatSession(Base):
    """Persisted chat session and optional workflow draft."""

    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    messages = Column(JSONB, nullable=False)
    workflow_draft = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

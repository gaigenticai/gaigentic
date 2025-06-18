"""Template model for marketplace."""
from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Column, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB

from ..database import Base


class Template(Base):
    """Prebuilt workflow template."""

    __tablename__ = "template"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(String(1024), nullable=False)
    workflow_draft = Column(JSONB, nullable=False)
    system_prompt = Column(Text, nullable=True)
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

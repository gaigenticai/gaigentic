"""Workflow execution logging model."""
from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID, JSONB

from ..database import Base


class ExecutionLog(Base):
    """Record of a workflow execution."""

    __tablename__ = "execution_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agent.id", ondelete="CASCADE"), nullable=False)
    workflow_snapshot = Column(JSONB, nullable=False)
    input_context = Column(JSONB, nullable=False)
    output_result = Column(JSONB, nullable=True)
    status = Column(String(32), nullable=False)
    duration_ms = Column(Integer, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=False)

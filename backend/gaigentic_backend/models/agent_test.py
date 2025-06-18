"""Agent test case model."""
from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID, JSONB

from ..database import Base


class AgentTest(Base):
    """Persisted agent test case."""

    __tablename__ = "agent_test"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agent.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    input_context = Column(JSONB, nullable=False)
    expected_output = Column(JSONB, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID

from ..database import Base


class Transaction(Base):
    """Financial transaction record."""

    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String(255), nullable=True)
    description = Column(String(1024), nullable=True)
    source_file_name = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

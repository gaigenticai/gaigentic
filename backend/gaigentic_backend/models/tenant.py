"""Tenant model."""
from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Column, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID

from ..database import Base


class Tenant(Base):
    """Tenant entity."""

    __tablename__ = "tenant"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

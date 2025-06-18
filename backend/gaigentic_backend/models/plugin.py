from __future__ import annotations

from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID

from ..database import Base


class Plugin(Base):
    """Custom plugin tool defined by a tenant."""

    __tablename__ = "plugin"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_plugin_name_per_tenant"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String(1024))
    code = Column(Text, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="SET NULL"))
    is_active = Column(Boolean, nullable=False, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

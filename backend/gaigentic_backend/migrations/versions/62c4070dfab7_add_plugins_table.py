"""add plugins table"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "62c4070dfab7"
down_revision = "4d2b8fb5041d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "plugin",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["user_account.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("tenant_id", "name", name="uq_plugin_name_per_tenant"),
    )


def downgrade() -> None:
    op.drop_table("plugin")

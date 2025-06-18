"""add transactions table"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "ad94e75a3fbe"
down_revision = "547a6a017bd2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("type", sa.String(length=255), nullable=True),
        sa.Column("description", sa.String(length=1024), nullable=True),
        sa.Column("source_file_name", sa.String(length=255), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("transactions")

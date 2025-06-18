"""add execution log table"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "1e8f2c9188f3"
down_revision = "0c2e03952e35"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "execution_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("workflow_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("input_context", postgresql.JSONB(), nullable=False),
        sa.Column("output_result", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenant.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agent.id"], ondelete="CASCADE"),
    )


def downgrade() -> None:
    op.drop_table("execution_log")

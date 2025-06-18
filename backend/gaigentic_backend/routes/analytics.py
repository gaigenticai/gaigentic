"""Analytics routes for execution monitoring."""
from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session
from ..models.agent import Agent
from ..models.transaction import Transaction
from ..models.execution_log import ExecutionLog
from ..services.tenant_context import get_current_tenant_id

router = APIRouter()


@router.get("/agents/{agent_id}/runs")
async def get_agent_runs(
    agent_id: UUID,
    session: AsyncSession = Depends(async_session),
    tenant_id: UUID = Depends(get_current_tenant_id),
) -> List[dict]:
    """Return recent execution logs for an agent."""

    query = (
        select(ExecutionLog.started_at, ExecutionLog.status, ExecutionLog.duration_ms)
        .where(
            ExecutionLog.agent_id == agent_id,
            ExecutionLog.tenant_id == tenant_id,
        )
        .order_by(ExecutionLog.started_at.desc())
        .limit(20)
    )
    result = await session.execute(query)
    return [dict(r) for r in result.all()]


@router.get("/tenants/{tenant_id}/stats")
async def tenant_stats(
    tenant_id: UUID,
    session: AsyncSession = Depends(async_session),
    current: UUID = Depends(get_current_tenant_id),
) -> dict:
    """Return aggregate statistics for a tenant."""

    if tenant_id != current:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    agent_count = await session.scalar(
        select(func.count(Agent.id)).where(Agent.tenant_id == tenant_id)
    )
    file_count = await session.scalar(
        select(func.count(func.distinct(Transaction.source_file_name))).where(
            Transaction.tenant_id == tenant_id
        )
    )
    exec_count = await session.scalar(
        select(func.count(ExecutionLog.id)).where(ExecutionLog.tenant_id == tenant_id)
    )
    avg_duration = await session.scalar(
        select(func.coalesce(func.avg(ExecutionLog.duration_ms), 0)).where(
            ExecutionLog.tenant_id == tenant_id
        )
    )
    return {
        "agents": agent_count or 0,
        "ingested_files": file_count or 0,
        "executions": exec_count or 0,
        "avg_duration_ms": int(avg_duration or 0),
    }


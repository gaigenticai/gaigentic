"""Prometheus metrics endpoint."""
from __future__ import annotations

import time
from fastapi import APIRouter, Depends, Response
from prometheus_client import CONTENT_TYPE_LATEST, Gauge, Histogram, generate_latest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session
from ..models.agent import Agent
from ..models.execution_log import ExecutionLog

START_TIME = time.time()
REQUEST_LATENCY = Histogram(
    "request_latency_seconds", "Request latency", ["method", "endpoint"]
)
UPTIME = Gauge("uptime_seconds", "Application uptime")
AGENTS = Gauge("agents_total", "Number of agents")
EXECUTIONS = Gauge("executions_total", "Number of executions")

router = APIRouter()


@router.get("/metrics")
async def metrics(session: AsyncSession = Depends(async_session)) -> Response:
    """Return Prometheus metrics."""
    AGENTS.set(await session.scalar(select(func.count(Agent.id))) or 0)
    EXECUTIONS.set(await session.scalar(select(func.count(ExecutionLog.id))) or 0)
    UPTIME.set(int(time.time() - START_TIME))
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)


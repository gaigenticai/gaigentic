"""Agent management routes."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session
from ..models.agent import Agent
from ..schemas.agent import AgentCreate, AgentOut
from ..services.tenant_context import get_current_tenant_id
from ..services.tool_executor import execute_tool

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=AgentOut, status_code=status.HTTP_201_CREATED)
async def create_agent(
    payload: AgentCreate,
    session: AsyncSession = Depends(async_session),
    tenant_id: UUID = Depends(get_current_tenant_id),
) -> AgentOut:
    """Create a new agent tied to the current tenant."""

    agent = Agent(name=payload.name, config=payload.config, tenant_id=tenant_id)
    session.add(agent)
    try:
        await session.commit()
        await session.refresh(agent)
    except SQLAlchemyError as exc:  # pragma: no cover - runtime path
        logger.exception("Failed to create agent: %s", exc)
        await session.rollback()
        raise HTTPException(status_code=500, detail="Could not create agent")
    return AgentOut.model_validate(agent)


@router.post("/{agent_id}/tools/{tool_name}/execute")
async def execute_agent_tool(
    agent_id: UUID,
    tool_name: str,
    input_data: dict,
) -> dict:
    """Execute a tool for the given agent."""

    return await execute_tool(agent_id, tool_name, input_data)

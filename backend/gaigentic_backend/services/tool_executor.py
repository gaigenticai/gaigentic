"""Utilities for executing tools via Superagent."""

from __future__ import annotations

import logging
from uuid import UUID

import httpx
from fastapi import HTTPException, status

from ..database import SessionLocal
from ..models.agent import Agent
from .superagent_client import get_superagent_client

logger = logging.getLogger(__name__)


async def execute_tool(agent_id: UUID, tool_name: str, input_data: dict, tenant_id: UUID) -> dict:
    """Execute a registered tool through Superagent."""
    async with SessionLocal() as session:  # type: AsyncSession
        agent = await session.get(Agent, agent_id)
        if agent is None or agent.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found"
            )

    logger.info(
        "Executing tool %s for agent %s (tenant %s)", tool_name, agent_id, tenant_id
    )

    async with get_superagent_client(str(tenant_id)) as client:
        try:
            response = await client.post(
                f"/agents/{agent_id}/tools/{tool_name}/run",
                json=input_data,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            logger.exception("Superagent request failed: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail="Tool execution failed"
            ) from exc
        except Exception as exc:  # pragma: no cover - unexpected runtime error
            logger.exception("Unexpected error executing tool: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unknown error",
            ) from exc

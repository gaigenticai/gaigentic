"""Utilities for executing tools via Superagent."""

from __future__ import annotations

import logging
from uuid import UUID

import httpx
from fastapi import HTTPException, status

from ..database import SessionLocal
from ..models.agent import Agent
from ..models.plugin import Plugin
from .superagent_client import get_superagent_client
from .plugin_executor import run_plugin
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
from fastapi import HTTPException
from ..database import SessionLocal


logger = logging.getLogger(__name__)



async def execute_tool(agent_id: UUID, tool_name: str, input_data: dict, tenant_id: UUID) -> dict:
    """Execute a registered tool through Superagent."""
    async with SessionLocal() as session:  # type: AsyncSession
        agent = await session.get(Agent, agent_id)
        if agent is None or agent.tenant_id != tenant_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

        if tool_name.startswith("plugin:"):
            plugin_id = UUID(tool_name.split(":", 1)[1])
            plugin = await session.get(Plugin, plugin_id)
            if plugin is None or plugin.tenant_id != tenant_id or not plugin.is_active:
                raise HTTPException(status_code=404, detail="Plugin not found")
            try:
                return await run_plugin(plugin.code, input_data)
            except Exception as exc:
                logger.exception("Plugin execution failed: %s", exc)
                raise HTTPException(status_code=400, detail=str(exc)) from exc

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

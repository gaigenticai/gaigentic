"""Agent management routes."""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..database import async_session
from ..models.agent import Agent
from ..schemas.agent import AgentCreate, AgentOut
from ..dependencies.auth import get_current_tenant_id, require_role
from ..services.tool_executor import execute_tool
from ..services.flow_validator import validate_workflow
from ..services.workflow_translator import translate_to_superagent
from ..services.superagent_client import get_superagent_client
from ..services.logging_executor import run_logged_workflow
from ..services.workflow_executor import run_workflow_stream
from ..schemas.chat import WorkflowDraft
import httpx

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=AgentOut, status_code=status.HTTP_201_CREATED)
async def create_agent(
    payload: AgentCreate,
    session: AsyncSession = Depends(async_session),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _user=Depends(require_role({"admin"})),
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
    tenant_id: UUID = Depends(get_current_tenant_id),
    _user=Depends(require_role({"admin", "user"})),
) -> dict:
    """Execute a tool for the given agent."""

    return await execute_tool(agent_id, tool_name, input_data, tenant_id)


@router.post("/{agent_id}/workflow")
async def save_workflow(
    agent_id: UUID,
    draft: WorkflowDraft,
    session: AsyncSession = Depends(async_session),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _user=Depends(require_role({"admin", "user"})),
) -> dict:
    """Validate and store a workflow for the agent."""

    agent = await session.get(Agent, agent_id)
    if agent is None or agent.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    try:
        validate_workflow(draft)
    except ValueError as exc:
        logger.error("Invalid workflow: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid workflow") from exc

    cfg = agent.config or {}
    cfg["workflow"] = draft.model_dump()
    agent.config = cfg
    try:
        await session.commit()
    except SQLAlchemyError as exc:  # pragma: no cover - runtime path
        logger.exception("Failed to store workflow: %s", exc)
        await session.rollback()
        raise HTTPException(status_code=500, detail="Could not store workflow") from exc

    logger.info("Workflow saved for agent %s", agent_id)
    return {"status": "saved"}


@router.post("/{agent_id}/deploy")
async def deploy_agent(
    agent_id: UUID,
    session: AsyncSession = Depends(async_session),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _user=Depends(require_role({"admin"})),
) -> dict:
    """Deploy the agent using its saved workflow."""

    agent = await session.get(Agent, agent_id)
    if agent is None or agent.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    workflow_data = (agent.config or {}).get("workflow")
    if not workflow_data:
        raise HTTPException(status_code=400, detail="No workflow defined")

    try:
        draft = WorkflowDraft.model_validate(workflow_data)
        superagent_payload = translate_to_superagent(draft)
    except ValueError as exc:
        logger.error("Workflow translation failed: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    logger.info("Deploying agent %s with payload %s", agent_id, superagent_payload)
    async with get_superagent_client(str(tenant_id)) as client:
        try:
            response = await client.post(f"/agents/{agent_id}/deploy", json=superagent_payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            logger.exception("Superagent deployment failed: %s", exc)
            raise HTTPException(status_code=502, detail="Deployment failed") from exc
        except Exception as exc:  # pragma: no cover
            logger.exception("Unexpected deployment error: %s", exc)
            raise HTTPException(status_code=500, detail="Unknown error") from exc

    return {"status": "deployed", "result": data}


@router.post("/{agent_id}/run")
async def execute_workflow(
    agent_id: UUID,
    input_context: dict,
    session: AsyncSession = Depends(async_session),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _user=Depends(require_role({"admin", "user"})),
) -> dict:
    """Execute the stored workflow for the agent and return step results."""

    agent = await session.get(Agent, agent_id)
    if agent is None or agent.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    return await run_logged_workflow(agent_id, input_context, tenant_id)


@router.post("/{agent_id}/simulate")
async def simulate_workflow(
    agent_id: UUID,
    input_context: dict,
    session: AsyncSession = Depends(async_session),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _user=Depends(require_role({"admin", "user"})),
) -> dict:
    """Execute the workflow without persistence and return trace."""

    agent = await session.get(Agent, agent_id)
    if agent is None or agent.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    trace: List[dict] = []
    async for step in run_workflow_stream(agent_id, input_context, tenant_id):
        trace.append(step)
    return {"trace": trace}


@router.websocket("/ws/agents/{agent_id}/run")
async def websocket_run_agent(
    websocket: WebSocket,
    agent_id: UUID,
    tenant_id: UUID,
    session_id: str | None = None,
) -> None:
    """Stream workflow execution events over WebSocket."""

    log_prefix = f"session {session_id} - " if session_id else ""
    await websocket.accept()
    ping_task = asyncio.create_task(_ping_loop(websocket))

    async with async_session() as session:
        agent = await session.get(Agent, agent_id)
        if agent is None or agent.tenant_id != tenant_id:
            await websocket.close(code=4004, reason="Agent not found")
            ping_task.cancel()
            return

    await websocket.send_json({"status": "started"})
    try:
        async for step in run_workflow_stream(agent_id, {}, tenant_id):
            logger.info("%snode %s complete", log_prefix, step["node_id"])
            await websocket.send_json(step)
        await websocket.send_json({"status": "complete"})
    except WebSocketDisconnect:
        logger.info("%sclient disconnected", log_prefix)
    except Exception as exc:  # pragma: no cover - runtime errors
        logger.exception("%serror running workflow: %s", log_prefix, exc)
        await websocket.close(code=1011, reason="server error")
    finally:
        ping_task.cancel()


async def _ping_loop(ws: WebSocket) -> None:
    """Send periodic pings to keep the WebSocket alive."""
    try:
        while True:
            await asyncio.sleep(15)
            await ws.send_json({"type": "ping"})
    except Exception:
        pass

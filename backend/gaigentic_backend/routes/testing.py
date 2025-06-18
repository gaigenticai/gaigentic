from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session
from ..models.agent import Agent
from ..models.agent_test import AgentTest
from ..schemas.agent_test import AgentTestCreate, AgentTestOut
from ..dependencies.auth import get_current_tenant_id, require_role
from ..services.test_runner import run_test

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agents")


@router.post("/{agent_id}/tests", response_model=AgentTestOut, status_code=status.HTTP_201_CREATED)
async def create_agent_test(
    agent_id: UUID,
    payload: AgentTestCreate,
    session: AsyncSession = Depends(async_session),
    user=Depends(require_role({"admin", "user"})),
    tenant_id: UUID = Depends(get_current_tenant_id),
) -> AgentTestOut:
    agent = await session.get(Agent, agent_id)
    if agent is None or agent.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Agent not found")

    count = await session.scalar(
        select(func.count(AgentTest.id)).where(AgentTest.agent_id == agent_id, AgentTest.tenant_id == tenant_id)
    )
    if count and count >= 50:
        raise HTTPException(status_code=400, detail="Test limit reached")

    test = AgentTest(
        tenant_id=tenant_id,
        agent_id=agent_id,
        name=payload.name,
        input_context=payload.input_context,
        expected_output=payload.expected_output,
        created_by=user.id,
    )
    session.add(test)
    try:
        await session.commit()
        await session.refresh(test)
    except SQLAlchemyError as exc:  # pragma: no cover - runtime path
        logger.exception("Failed to create test: %s", exc)
        await session.rollback()
        raise HTTPException(status_code=500, detail="Could not create test") from exc
    return AgentTestOut.model_validate(test)


@router.post("/{agent_id}/tests/{test_id}/run")
async def run_agent_test(
    agent_id: UUID,
    test_id: UUID,
    session: AsyncSession = Depends(async_session),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _user=Depends(require_role({"admin", "user"})),
) -> dict:
    test = await session.get(AgentTest, test_id)
    if test is None or test.agent_id != agent_id or test.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Test not found")
    return await run_test(agent_id, test.input_context, test.expected_output, tenant_id)


@router.get("/{agent_id}/tests", response_model=list[AgentTestOut])
async def list_agent_tests(
    agent_id: UUID,
    session: AsyncSession = Depends(async_session),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _user=Depends(require_role({"admin", "user", "readonly"})),
) -> list[AgentTestOut]:
    result = await session.execute(
        select(AgentTest).where(AgentTest.agent_id == agent_id, AgentTest.tenant_id == tenant_id).order_by(AgentTest.created_at)
    )
    tests = result.scalars().all()
    return [AgentTestOut.model_validate(t) for t in tests]


@router.delete("/{agent_id}/tests/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent_test(
    agent_id: UUID,
    test_id: UUID,
    session: AsyncSession = Depends(async_session),
    tenant_id: UUID = Depends(get_current_tenant_id),
    user=Depends(require_role({"admin", "user"})),
) -> None:
    test = await session.get(AgentTest, test_id)
    if test is None or test.agent_id != agent_id or test.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Test not found")
    if test.created_by != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    await session.delete(test)
    await session.commit()


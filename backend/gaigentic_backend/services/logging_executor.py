"""Workflow execution with runtime logging."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import SessionLocal
from ..models.execution_log import ExecutionLog
from .workflow_executor import _load_agent, run_workflow

logger = logging.getLogger(__name__)


async def run_logged_workflow(agent_id: UUID, input_context: Dict[str, Any], tenant_id: UUID) -> Dict[str, Any]:
    """Execute a workflow and persist an execution log."""
    started = datetime.now(tz=timezone.utc)
    status = "success"
    output: Dict[str, Any] | None = None
    workflow_snapshot: Dict[str, Any] | None = None

    try:
        agent = await _load_agent(agent_id, tenant_id)
        workflow_snapshot = (agent.config or {}).get("workflow") or {}
        output = await run_workflow(agent_id, input_context, tenant_id)
        status = "success"
        return output
    except HTTPException as exc:
        status = "failure" if 400 <= exc.status_code < 500 else "error"
        raise
    except Exception:
        status = "error"
        raise
    finally:
        finished = datetime.now(tz=timezone.utc)
        duration_ms = int((finished - started).total_seconds() * 1000)
        log_output: Any = output
        try:
            serialized = json.dumps(output or {}).encode()
            if len(serialized) > 100_000:
                log_output = {"truncated": True}
        except Exception:
            log_output = {"error": "unserializable"}

        log_entry = ExecutionLog(
            tenant_id=tenant_id,
            agent_id=agent_id,
            workflow_snapshot=workflow_snapshot or {},
            input_context=input_context,
            output_result=log_output,
            status=status,
            duration_ms=duration_ms,
            started_at=started,
            finished_at=finished,
        )
        async with SessionLocal() as session:  # type: AsyncSession
            session.add(log_entry)
            try:
                await session.commit()
            except Exception:  # pragma: no cover - runtime commit failure
                logger.exception("Failed to store execution log")
                await session.rollback()


"""Chat to workflow builder routes."""
from __future__ import annotations

import json
import logging
from uuid import UUID

import asyncio
import time
from collections import deque
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session
from ..models.chat_session import ChatSession
from ..schemas.chat import ChatRequest, ChatResponse
from ..services.flow_validator import validate_workflow
from ..services.llm_chat import ChatSME
from ..dependencies.auth import get_current_tenant_id, require_role

logger = logging.getLogger(__name__)

router = APIRouter()

_RATE_LIMIT: dict[str, deque[float]] = {}


@router.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(
    payload: ChatRequest,
    session: AsyncSession = Depends(async_session),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _user=Depends(require_role({"admin", "user"})),
) -> ChatResponse:
    """Handle chat messages and optionally store workflow drafts."""

    llm = ChatSME()
    try:
        response = await llm.chat(payload.messages)
    except Exception as exc:  # pragma: no cover - runtime errors
        logger.exception("LLM chat failed: %s", exc)
        raise HTTPException(status_code=500, detail="LLM error")

    if response.workflow_draft is not None:
        try:
            validate_workflow(response.workflow_draft)
        except ValueError as exc:
            logger.error("Invalid workflow draft: %s", exc)
            raise HTTPException(status_code=400, detail="Invalid workflow draft") from exc

    session_obj = ChatSession(
        tenant_id=tenant_id,
        messages=json.loads(ChatRequest.model_dump_json(payload)),
        workflow_draft=(response.workflow_draft.model_dump() if response.workflow_draft else None),
    )
    session.add(session_obj)
    try:
        await session.commit()
    except SQLAlchemyError as exc:  # pragma: no cover - runtime path
        logger.exception("Failed to store chat session: %s", exc)
        await session.rollback()

    return response


@router.websocket("/ws/chat")
async def chat_websocket(
    websocket: WebSocket,
    session_id: str | None = None,
) -> None:
    """Handle chat streaming over WebSocket."""

    log_prefix = f"session {session_id} - " if session_id else ""
    await websocket.accept()
    ping_task = asyncio.create_task(_ping_loop(websocket))

    try:
        raw = await websocket.receive_text()
        data = json.loads(raw)
        payload = ChatRequest.model_validate(data)

        client = websocket.client.host if websocket.client else "anon"
        dq = _RATE_LIMIT.setdefault(client, deque())
        now = time.time()
        while dq and now - dq[0] > 60:
            dq.popleft()
        if len(dq) >= 2:
            await websocket.close(code=4008, reason="rate limit")
            ping_task.cancel()
            return
        dq.append(now)

        llm = ChatSME()
        response = await llm.chat(payload.messages)

        reply = response.reply.split()
        accumulated = ""
        for token in reply:
            accumulated += token + " "
            await websocket.send_json({"token": token})
        final = {"status": "complete"}
        if response.workflow_draft is not None:
            final["workflow_draft"] = response.workflow_draft.model_dump()
        await websocket.send_json(final)
    except WebSocketDisconnect:
        logger.info("%sclient disconnected", log_prefix)
    except Exception as exc:  # pragma: no cover - runtime errors
        logger.exception("%swebsocket chat error: %s", log_prefix, exc)
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

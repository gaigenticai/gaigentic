"""Chat to workflow builder routes."""
from __future__ import annotations

import json
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session
from ..models.chat_session import ChatSession
from ..schemas.chat import ChatRequest, ChatResponse
from ..services.flow_validator import validate_workflow
from ..services.llm_chat import ChatSME
from ..services.tenant_context import get_current_tenant_id

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/api/v1/chat", response_model=ChatResponse)
async def chat_endpoint(
    payload: ChatRequest,
    session: AsyncSession = Depends(async_session),
    tenant_id: UUID = Depends(get_current_tenant_id),
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

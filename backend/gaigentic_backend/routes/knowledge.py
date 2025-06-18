from __future__ import annotations

import logging
import time
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import async_session
from ..models.agent import Agent
from ..models.knowledge_chunk import KnowledgeChunk
from ..dependencies.auth import get_current_tenant_id, require_role
from ..services.file_loader import load_file
from ..services.chunking import split_text
from ..services.embedding import get_embedding

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/agents/{agent_id}/knowledge/upload")
async def upload_knowledge(
    agent_id: UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(async_session),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _user=Depends(require_role({"admin", "user"})),
) -> dict:
    """Upload a knowledge file and store vector chunks."""

    start = time.time()
    agent = await session.get(Agent, agent_id)
    if agent is None or agent.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    text = await load_file(file)
    parts = split_text(text, max_tokens=500)

    records: List[KnowledgeChunk] = []
    for idx, chunk in enumerate(parts):
        embedding = await get_embedding(chunk)
        records.append(
            KnowledgeChunk(
                tenant_id=tenant_id,
                agent_id=agent_id,
                source_file=file.filename or "",
                chunk_index=idx,
                text=chunk,
                embedding=embedding,
            )
        )

    session.add_all(records)
    try:
        await session.commit()
    except Exception as exc:  # pragma: no cover - runtime path
        logger.exception("Failed to store knowledge chunks: %s", exc)
        await session.rollback()
        raise HTTPException(status_code=500, detail="Could not store knowledge") from exc

    elapsed = int((time.time() - start) * 1000)
    logger.info(
        "Ingested %s chunks from %s for agent %s in %sms", len(records), file.filename, agent_id, elapsed
    )
    return {"chunks": len(records)}


@router.get("/agents/{agent_id}/knowledge/search")
async def search_knowledge(
    agent_id: UUID,
    q: str,
    session: AsyncSession = Depends(async_session),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _user=Depends(require_role({"admin", "user", "readonly"})),
) -> List[dict]:
    """Return top 5 knowledge chunks most similar to the query."""

    agent = await session.get(Agent, agent_id)
    if agent is None or agent.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    query_vec = await get_embedding(q)
    stmt = (
        select(KnowledgeChunk.source_file, KnowledgeChunk.chunk_index, KnowledgeChunk.text)
        .where(
            KnowledgeChunk.agent_id == agent_id,
            KnowledgeChunk.tenant_id == tenant_id,
        )
        .order_by(KnowledgeChunk.embedding.cosine_distance(query_vec))
        .limit(5)
    )
    result = await session.execute(stmt)
    return [dict(r) for r in result.all()]

"""Utilities for retrieving and storing agent memory."""

from __future__ import annotations

import logging
from typing import Dict, List
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import tiktoken

from ..database import SessionLocal
from ..models.agent import Agent
from ..models.message_history import MessageHistory
from ..models.knowledge_chunk import KnowledgeChunk
from ..services.embedding import get_embedding
from ..config import settings

logger = logging.getLogger(__name__)

_ENCODER = tiktoken.get_encoding("cl100k_base")
_MAX_TOKENS = 1800


def _count_tokens(text: str) -> int:
    return len(_ENCODER.encode(text))


async def store_message(agent_id: UUID, role: str, content: str) -> None:
    """Persist a chat message with its embedding."""

    embedding = await get_embedding(content)
    async with SessionLocal() as session:  # type: AsyncSession
        agent = await session.get(Agent, agent_id)
        if agent is None:
            logger.error("Agent %s not found when storing message", agent_id)
            return
        record = MessageHistory(
            tenant_id=agent.tenant_id,
            agent_id=agent_id,
            role=role,
            content=content,
            embedding=embedding,
        )
        session.add(record)
        try:
            await session.commit()
        except Exception as exc:  # pragma: no cover - runtime failure
            logger.exception("Failed to store message: %s", exc)
            await session.rollback()


async def fetch_context_for_agent(
    agent_id: UUID,
    current_user_message: str,
    chat_k: int = settings.memory_chat_k_default,
    semantic_k: int = settings.memory_semantic_k_default,
) -> List[Dict]:
    """Return combined chat and semantic memory for an agent."""

    query_vec = await get_embedding(current_user_message)
    async with SessionLocal() as session:  # type: AsyncSession
        chat_stmt = (
            select(
                MessageHistory.role,
                MessageHistory.content,
                MessageHistory.created_at,
            )
            .where(MessageHistory.agent_id == agent_id)
            .order_by(MessageHistory.created_at.desc())
            .limit(chat_k)
        )
        chat_res = await session.execute(chat_stmt)
        chat_messages = [dict(r) for r in chat_res.all()]
        chat_messages.reverse()

        kc_stmt = (
            select(
                KnowledgeChunk.text.label("content"),
                KnowledgeChunk.created_at,
            )
            .where(KnowledgeChunk.agent_id == agent_id)
            .where(KnowledgeChunk.embedding.cosine_distance(query_vec) < 0.35)
            .order_by(KnowledgeChunk.embedding.cosine_distance(query_vec))
            .limit(semantic_k)
        )
        kc_res = await session.execute(kc_stmt)
        knowledge_hits = [
            {"role": "system", "content": r.content, "created_at": r.created_at}
            for r in kc_res.all()
        ]

        hist_stmt = (
            select(
                MessageHistory.role,
                MessageHistory.content,
                MessageHistory.created_at,
            )
            .where(MessageHistory.agent_id == agent_id)
            .where(MessageHistory.embedding.cosine_distance(query_vec) < 0.35)
            .order_by(MessageHistory.embedding.cosine_distance(query_vec))
            .limit(semantic_k)
        )
        hist_res = await session.execute(hist_stmt)
        semantic_hits = [dict(r) for r in hist_res.all()]

    combined = chat_messages + knowledge_hits + semantic_hits
    combined.sort(key=lambda r: r["created_at"])  # chronological
    seen = set()
    deduped: List[Dict] = []
    for r in combined:
        if r["content"] in seen:
            continue
        deduped.append({"role": r["role"], "content": r["content"], "created_at": r["created_at"]})
        seen.add(r["content"])

    total = 0
    trimmed: List[Dict] = []
    for r in reversed(deduped):
        tokens = _count_tokens(r["content"])
        if total + tokens > _MAX_TOKENS:
            break
        trimmed.append(r)
        total += tokens
    trimmed.reverse()
    return [{"role": r["role"], "content": r["content"]} for r in trimmed]

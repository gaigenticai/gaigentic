from __future__ import annotations

import logging
from typing import List

import openai

from ..config import settings

logger = logging.getLogger(__name__)


async def get_embedding(text: str) -> List[float]:
    """Return embedding vector for the given text."""

    if not settings.openai_api_key:
        raise RuntimeError("OpenAI API key not configured")

    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    try:
        resp = await client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
    except Exception as exc:  # pragma: no cover - runtime errors
        logger.exception("Embedding request failed: %s", exc)
        raise
    return resp.data[0].embedding

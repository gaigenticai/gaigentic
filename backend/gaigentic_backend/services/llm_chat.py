"""LLM-powered chat service."""
from __future__ import annotations

import logging
from typing import List

from ..config import settings
from ..schemas.chat import ChatMessage, ChatResponse, WorkflowDraft
from ..services.llm_router import run_llm

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Act as a BFSI subject-matter expert. Ask any clarifying questions needed. "
    "Once enough info is gathered, return a valid JSON block labelled WORKFLOW_DRAFT "
    "containing nodes and edges representing the agentic workflow."
)


class ChatSME:
    """Wrapper around LLM chat completion APIs."""

    def __init__(
        self,
        provider: str | None = None,
        model: str | None = None,
        temperature: float = 0.2,
        max_tokens: int | None = None,
    ) -> None:
        self.provider = provider or settings.llm_provider
        self.model = model or settings.llm_model
        if temperature > 0.7:
            raise ValueError("temperature may not exceed 0.7")
        self.temperature = temperature
        self.max_tokens = max_tokens
        if self.provider not in settings.llm_providers_enabled:
            raise ValueError("provider not enabled")

    async def chat(self, messages: List[ChatMessage]) -> ChatResponse:
        """Send chat messages to the LLM and return the response."""

        history = [
            {"role": m.role, "content": m.content}
            for m in messages
        ]
        history.insert(0, {"role": "system", "content": _SYSTEM_PROMPT})
        logger.info("Sending %s messages to LLM", len(history))
        content = await run_llm(
            self.provider,
            self.model,
            history,
            {"temperature": self.temperature, "max_tokens": self.max_tokens},
        )
        logger.debug("LLM raw response: %s", content)
        reply, draft = _extract_draft(content)
        return ChatResponse(reply=reply, workflow_draft=draft)


def _extract_draft(content: str) -> tuple[str, WorkflowDraft | None]:
    """Parse workflow draft from the assistant content."""

    import json
    import re

    pattern = r"```json\\s*WORKFLOW_DRAFT(?P<json>{.*?})```"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return content, None
    json_str = match.group("json")
    try:
        data = json.loads(json_str)
        draft = WorkflowDraft.model_validate(data)
        reply_text = content.replace(match.group(0), "").strip()
        return reply_text, draft
    except Exception as exc:  # pragma: no cover - runtime parsing error
        logger.exception("Failed to parse workflow draft: %s", exc)
        return content, None

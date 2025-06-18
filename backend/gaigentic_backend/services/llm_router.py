from __future__ import annotations

"""Routing logic for multiple LLM providers."""

import logging
from typing import Any, List

import httpx
import openai

from ..config import settings

logger = logging.getLogger(__name__)


async def _post_json(url: str, headers: dict[str, str], payload: dict[str, Any]) -> httpx.Response:
    client = httpx.AsyncClient(timeout=20)
    try:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        return resp
    finally:
        await client.aclose()


async def run_llm(provider: str, model: str, messages: List[dict[str, Any]], config: dict) -> str:
    """Execute a chat completion call for the given provider."""

    if provider not in settings.llm_providers_enabled:
        raise ValueError("provider not enabled")

    temperature = config.get("temperature", 0.2)
    max_tokens = config.get("max_tokens")

    for attempt in range(2):
        try:
            if provider == "openai":
                client = openai.AsyncOpenAI(api_key=settings.openai_api_key, timeout=20)
                resp = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return resp.choices[0].message.content if resp.choices else ""

            if provider == "anthropic":
                if not settings.claude_api_key:
                    raise RuntimeError("Anthropic API key not configured")
                resp = await _post_json(
                    "https://api.anthropic.com/v1/messages",
                    {
                        "x-api-key": settings.claude_api_key,
                        "anthropic-version": "2023-06-01",
                    },
                    {
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                data = resp.json()
                return data.get("content", [{}])[0].get("text", "")

            if provider == "mistral":
                if not settings.mistral_api_key:
                    raise RuntimeError("Mistral API key not configured")
                resp = await _post_json(
                    "https://api.mistral.ai/v1/chat/completions",
                    {"Authorization": f"Bearer {settings.mistral_api_key}"},
                    {
                        "model": model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    },
                )
                data = resp.json()
                return data["choices"][0]["message"]["content"]

            if provider == "ollama":
                base = settings.ollama_base_url or "http://localhost:11434"
                resp = await _post_json(
                    f"{base}/api/chat",
                    {},
                    {"model": model, "messages": messages, "temperature": temperature},
                )
                return resp.json().get("message", {}).get("content", "")

            raise ValueError("invalid provider")
        except httpx.HTTPStatusError as exc:  # transient HTTP errors
            if attempt == 0 and 500 <= exc.response.status_code < 600:
                logger.warning("LLM %s call retry due to %s", provider, exc.response.status_code)
                continue
            raise
        except Exception as exc:  # pragma: no cover - runtime path
            if attempt == 0:
                logger.warning("LLM %s call retry after error: %s", provider, exc)
                continue
            raise

    return ""  # fallback

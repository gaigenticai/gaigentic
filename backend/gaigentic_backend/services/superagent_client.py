"""Client for communicating with Superagent."""

from __future__ import annotations

import httpx

from ..config import SUPERAGENT_API_KEY_PREFIX, settings


class SuperagentClient:
    """Thin wrapper around ``httpx.AsyncClient`` with auth headers."""

    def __init__(self, base_url: str, api_key: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    async def post(self, url: str, json: dict) -> httpx.Response:
        """Send a POST request."""

        return await self._client.post(url, json=json)

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""

        await self._client.aclose()

    async def __aenter__(self) -> "SuperagentClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - cleanup
        await self.aclose()


def get_superagent_client(tenant_id: str) -> SuperagentClient:
    """Return a client instance for the given tenant."""

    api_key = f"{SUPERAGENT_API_KEY_PREFIX}{tenant_id}_key"
    return SuperagentClient(settings.superagent_url, api_key)

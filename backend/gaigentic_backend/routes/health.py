"""Health check endpoint."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
async def healthcheck() -> dict[str, str]:
    """Return service health status."""
    return {"status": "ok"}

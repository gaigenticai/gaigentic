"""Application routers."""
from fastapi import APIRouter

from . import health, auth

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/api/v1/auth")

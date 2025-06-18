"""Application routers."""
from fastapi import APIRouter

from . import health, auth, knowledge

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router, prefix="/api/v1/auth")
api_router.include_router(knowledge.router, prefix="/api/v1")

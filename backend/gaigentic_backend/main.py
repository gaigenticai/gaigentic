"""Gaigentic FastAPI application."""

from __future__ import annotations

import logging
import uuid
import os

import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from sqlalchemy import text, select

from .database import engine, SessionLocal
from .routes import (
    api_router,
    agents,
    ingestion,
    chat,
    analytics,
    auth,
    templates,
    knowledge,
    plugins,
    testing,
)
from .routes.metrics import REQUEST_LATENCY
from .middleware import RateLimitMiddleware, MetricsMiddleware
from .models.user import User, RoleEnum
from .models.tenant import Tenant
from .config import settings
from .services.security import hash_password

logger = logging.getLogger(__name__)

if settings.log_file and settings.app_env == "production":
    os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
    logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler(settings.log_file), logging.StreamHandler(sys.stdout)])


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Ensure each request contains an ``X-Request-ID`` header."""

    async def dispatch(self, request: Request, call_next):
        if "X-Request-ID" not in request.headers:
            request_id = str(uuid.uuid4())
            request.scope["headers"].append((b"x-request-id", request_id.encode()))
        response = await call_next(request)
        return response


async def lifespan(app: FastAPI):
    """Application lifespan to verify DB connectivity."""

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
    except Exception as exc:  # pragma: no cover - executed on startup
        logger.exception("Database connection failed: %s", exc)
        raise

    if settings.app_env == "local":
        async with SessionLocal() as session:
            exists = await session.scalar(select(User).where(User.email == "admin@gaigentic.ai"))
            if not exists:
                tenant = Tenant(name="DevTenant")
                session.add(tenant)
                await session.flush()
                user = User(
                    tenant_id=tenant.id,
                    email="admin@gaigentic.ai",
                    password_hash=hash_password("gaigentic123"),
                    role=RoleEnum.admin,
                )
                session.add(user)
                await session.commit()

    yield


app = FastAPI(title="Gaigentic Backend", lifespan=lifespan)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(MetricsMiddleware, histogram=REQUEST_LATENCY)
app.add_middleware(RateLimitMiddleware, max_requests=settings.rate_limit_per_minute)
if settings.app_env == "production":
    app.add_middleware(HTTPSRedirectMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o],
    allow_methods=["*"],
    allow_headers=["*"]
)
app.include_router(api_router)
app.include_router(auth.router, prefix="/api/v1/auth")
app.include_router(agents.router, prefix="/api/v1/agents")
app.include_router(ingestion.router, prefix="/api/v1/ingest")
app.include_router(chat.router)
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(templates.router)
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(plugins.router, prefix="/api/v1/plugins")
app.include_router(testing.router)

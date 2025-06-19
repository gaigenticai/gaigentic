from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session
from ..models.plugin import Plugin
from ..schemas.plugin import PluginCreate, PluginOut
from ..dependencies.auth import get_current_tenant_id, require_role
from ..services.plugin_executor import run_plugin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/plugins")


@router.post("/", response_model=PluginOut, status_code=status.HTTP_201_CREATED)
async def create_plugin(
    payload: PluginCreate,
    session: AsyncSession = Depends(async_session),
    user=Depends(require_role({"admin"})),
    tenant_id: UUID = Depends(get_current_tenant_id),
) -> PluginOut:
    exists = await session.scalar(
        select(Plugin.id).where(Plugin.tenant_id == tenant_id, Plugin.name == payload.name)
    )
    if exists:
        raise HTTPException(status_code=400, detail="Plugin name already exists")
    try:
        await run_plugin(payload.code, {})
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    plugin = Plugin(
        tenant_id=tenant_id,
        name=payload.name,
        description=payload.description,
        code=payload.code,
        created_by=user.id,
        is_active=True,
    )
    session.add(plugin)
    try:
        await session.commit()
        await session.refresh(plugin)
    except SQLAlchemyError as exc:  # pragma: no cover - runtime path
        logger.exception("Failed to create plugin: %s", exc)
        await session.rollback()
        raise HTTPException(status_code=500, detail="Could not create plugin") from exc
    return PluginOut.model_validate(plugin)


@router.get("/", response_model=list[PluginOut])
async def list_plugins(
    session: AsyncSession = Depends(async_session),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _user=Depends(require_role({"admin", "user", "readonly"})),
) -> list[PluginOut]:
    result = await session.execute(
        select(Plugin).where(Plugin.tenant_id == tenant_id, Plugin.is_active == True)
    )
    plugins = result.scalars().all()
    return [PluginOut.model_validate(p) for p in plugins]


@router.post("/{plugin_id}/test")
async def test_plugin(
    plugin_id: UUID,
    input_data: dict,
    session: AsyncSession = Depends(async_session),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _user=Depends(require_role({"admin", "user"})),
) -> dict:
    plugin = await session.get(Plugin, plugin_id)
    if plugin is None or plugin.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Plugin not found")
    if not plugin.is_active:
        raise HTTPException(status_code=400, detail="Plugin disabled")
    try:
        return await run_plugin(plugin.code, input_data)
    except Exception as exc:  # pragma: no cover - runtime failure
        logger.exception("Plugin test failed: %s", exc)
        return {"error": str(exc)}


@router.post("/{plugin_id}/disable")
async def toggle_plugin(
    plugin_id: UUID,
    session: AsyncSession = Depends(async_session),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _user=Depends(require_role({"admin"})),
) -> dict:
    plugin = await session.get(Plugin, plugin_id)
    if plugin is None or plugin.tenant_id != tenant_id:
        raise HTTPException(status_code=404, detail="Plugin not found")
    plugin.is_active = not plugin.is_active
    try:
        await session.commit()
    except SQLAlchemyError as exc:  # pragma: no cover - runtime path
        logger.exception("Failed to toggle plugin: %s", exc)
        await session.rollback()
        raise HTTPException(status_code=500, detail="Could not update plugin") from exc
    status_str = "enabled" if plugin.is_active else "disabled"
    return {"status": status_str}


@router.delete(
    "/{plugin_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response  # ✅ this tells FastAPI not to expect a body
)
async def purge_plugin(
    plugin_id: UUID,
    session: AsyncSession = Depends(async_session),
    _user=Depends(require_role({"admin"})),
) -> Response:
    plugin = await session.get(Plugin, plugin_id)
    if plugin is None:
        raise HTTPException(status_code=404, detail="Plugin not found")
    await session.delete(plugin)
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

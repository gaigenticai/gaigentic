"""Template marketplace routes."""
from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session
from ..models.template import Template
from ..models.agent import Agent
from ..schemas.template import TemplateCreate, TemplateOut
from ..schemas.chat import WorkflowDraft
from ..services.flow_validator import validate_workflow
from ..dependencies.auth import get_current_tenant_id, require_role

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/templates")


@router.get("/", response_model=list[TemplateOut])
async def list_templates(
    session: AsyncSession = Depends(async_session),
    _user=Depends(require_role({"admin", "user", "readonly"})),
) -> list[TemplateOut]:
    """Return all templates."""

    result = await session.execute(select(Template))
    templates = result.scalars().all()
    return [TemplateOut.model_validate(t) for t in templates]


@router.get("/{template_id}", response_model=TemplateOut)
async def get_template(
    template_id: UUID,
    session: AsyncSession = Depends(async_session),
    _user=Depends(require_role({"admin", "user", "readonly"})),
) -> TemplateOut:
    """Fetch a single template."""

    template = await session.get(Template, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return TemplateOut.model_validate(template)


@router.post("/", response_model=TemplateOut, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: TemplateCreate,
    session: AsyncSession = Depends(async_session),
    user=Depends(require_role({"admin"})),
) -> TemplateOut:
    """Create a new template (admins only)."""

    exists = await session.scalar(select(Template.id).where(Template.name == payload.name))
    if exists:
        raise HTTPException(status_code=400, detail="Template name already exists")

    try:
        validate_workflow(payload.workflow_draft)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid workflow") from exc

    prompt = payload.system_prompt or None
    if prompt and len(prompt) > 10 * 1024:
        prompt = prompt[: 10 * 1024]

    template = Template(
        name=payload.name,
        description=payload.description,
        workflow_draft=payload.workflow_draft.model_dump(),
        system_prompt=prompt,
        created_by=user.email,
    )
    session.add(template)
    try:
        await session.commit()
        await session.refresh(template)
    except SQLAlchemyError as exc:
        logger.exception("Failed to create template: %s", exc)
        await session.rollback()
        raise HTTPException(status_code=500, detail="Could not create template")

    return TemplateOut.model_validate(template)


@router.post("/{template_id}/clone", status_code=status.HTTP_201_CREATED)
async def clone_template(
    template_id: UUID,
    session: AsyncSession = Depends(async_session),
    tenant_id: UUID = Depends(get_current_tenant_id),
    _user=Depends(require_role({"admin", "user"})),
) -> dict:
    """Clone a template into a new agent for the tenant."""

    template = await session.get(Template, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    draft_dict = template.workflow_draft
    try:
        draft = WorkflowDraft.model_validate(draft_dict)
        validate_workflow(draft)
    except ValueError as exc:
        logger.error("Invalid template workflow: %s", exc)
        raise HTTPException(status_code=400, detail="Invalid template") from exc

    agent = Agent(
        tenant_id=tenant_id,
        name=template.name,
        config={"workflow": draft_dict, "system_prompt": template.system_prompt},
    )
    session.add(agent)
    try:
        await session.commit()
        await session.refresh(agent)
    except SQLAlchemyError as exc:
        logger.exception("Failed to clone template: %s", exc)
        await session.rollback()
        raise HTTPException(status_code=500, detail="Could not clone template")

    return {"agent_id": str(agent.id)}

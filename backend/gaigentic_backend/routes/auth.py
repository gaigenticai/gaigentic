from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from ..database import async_session
from ..models.user import User, RoleEnum
from ..models.tenant import Tenant
from ..services.security import create_access_token, hash_password, verify_password
from ..dependencies.auth import get_current_user

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_name: str


class TokenRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/register", response_model=TokenResponse)
async def register_user(
    payload: RegisterRequest,
    session: AsyncSession = Depends(async_session),
) -> TokenResponse:
    existing = await session.scalar(select(User).where(User.email == payload.email))
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    tenant = Tenant(name=payload.tenant_name)
    session.add(tenant)
    await session.flush()
    user = User(
        tenant_id=tenant.id,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=RoleEnum.admin,
    )
    session.add(user)
    await session.commit()
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)


@router.post("/token", response_model=TokenResponse)
async def login(payload: TokenRequest, session: AsyncSession = Depends(async_session)) -> TokenResponse:
    user = await session.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "tenant_id": str(user.tenant_id),
        "role": user.role.value if isinstance(user.role, RoleEnum) else user.role,
        "created_at": user.created_at.isoformat(),
    }

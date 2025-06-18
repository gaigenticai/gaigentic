from __future__ import annotations

from typing import Iterable
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import async_session
from ..models.user import User, RoleEnum
from ..services.security import decode_access_token

http_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(http_scheme),
    session: AsyncSession = Depends(async_session),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id = UUID(payload.get("sub"))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def require_role(roles: Iterable[str]):
    async def dependency(user: User = Depends(get_current_user)) -> User:
        role_val = user.role.value if isinstance(user.role, RoleEnum) else user.role
        if role_val not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return user

    return dependency


async def get_current_tenant_id(user: User = Depends(get_current_user)) -> UUID:
    return user.tenant_id

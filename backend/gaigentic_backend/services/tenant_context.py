"""Tenant context utilities."""
from __future__ import annotations

from uuid import UUID


async def get_current_tenant_id() -> UUID:
    """Return the current tenant ID.

    This is a placeholder implementation and will later be replaced with
    authentication logic.
    """

    # TODO: replace with real tenant resolution
    return UUID("00000000-0000-0000-0000-000000000001")

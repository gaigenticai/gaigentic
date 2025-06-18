from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TransactionIngested(BaseModel):
    date: datetime
    amount: float
    description: str | None = None
    type: str | None = None


class TransactionRecord(BaseModel):
    id: UUID
    tenant_id: UUID
    date: datetime
    amount: float
    description: str | None = None
    type: str | None = None
    source_file_name: str
    uploaded_at: datetime

    model_config = {
        "json_encoders": {datetime: lambda v: v.isoformat()},
    }

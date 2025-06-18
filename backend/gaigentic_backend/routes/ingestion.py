from __future__ import annotations

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session
from ..models.transaction import Transaction
from ..services.file_parser import parse_file
from ..services.tenant_context import get_current_tenant_id

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def ingest_transactions(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(async_session),
    tenant_id: UUID = Depends(get_current_tenant_id),
) -> dict:
    """Upload a CSV or XLSX file and store transactions."""

    records = parse_file(file)
    transactions: List[Transaction] = []
    for rec in records:
        transactions.append(
            Transaction(
                tenant_id=tenant_id,
                date=rec["date"],
                amount=rec["amount"],
                description=rec.get("description"),
                type=rec.get("type"),
                source_file_name=file.filename or "",
            )
        )

    session.add_all(transactions)
    try:
        await session.commit()
    except SQLAlchemyError as exc:  # pragma: no cover - runtime path
        logger.exception("Failed to ingest transactions: %s", exc)
        await session.rollback()
        raise HTTPException(status_code=500, detail="Could not store transactions")

    row_count = len(transactions)
    logger.info(
        "Ingested %s transactions from %s for tenant %s", row_count, file.filename, tenant_id
    )
    return {"rows_imported": row_count}

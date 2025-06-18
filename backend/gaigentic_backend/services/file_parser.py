from __future__ import annotations

import os
import logging
from typing import List, Dict
import pandas as pd
from fastapi import UploadFile, HTTPException, status

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def _validate_columns(df: pd.DataFrame) -> None:
    required = {"date", "amount", "description"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing required columns: {', '.join(sorted(missing))}",
        )


def parse_file(file: UploadFile) -> List[Dict]:
    """Parse an uploaded CSV or XLSX file into transaction records."""

    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large")

    filename = (file.filename or "").lower()
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(file.file)
        elif filename.endswith(".xlsx"):
            df = pd.read_excel(file.file)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")
    except Exception as exc:  # pragma: no cover - runtime parsing errors
        logger.exception("Failed to parse uploaded file: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file format") from exc

    _validate_columns(df)

    records: List[Dict] = []
    for _, row in df.iterrows():
        try:
            date = pd.to_datetime(row["date"]).to_pydatetime()
        except Exception:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid date value")
        try:
            amount = float(row["amount"])
        except Exception:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid amount value")
        record = {
            "date": date,
            "amount": amount,
            "description": None if pd.isna(row.get("description")) else str(row.get("description")),
            "type": None if pd.isna(row.get("type")) else str(row.get("type")),
        }
        records.append(record)

    return records

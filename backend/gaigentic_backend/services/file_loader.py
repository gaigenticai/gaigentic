from __future__ import annotations

import os
import logging
from io import BytesIO

from fastapi import UploadFile, HTTPException, status
import fitz  # PyMuPDF
from docx import Document

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


async def load_file(file: UploadFile) -> str:
    """Extract plain text from an uploaded file."""

    file.file.seek(0, os.SEEK_END)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File too large")

    filename = (file.filename or "").lower()
    try:
        if filename.endswith(".pdf"):
            data = await file.read()
            doc = fitz.open(stream=data, filetype="pdf")
            text = "".join(page.get_text() for page in doc)
            doc.close()
        elif filename.endswith(".docx"):
            data = await file.read()
            doc = Document(BytesIO(data))
            text = "\n".join(p.text for p in doc.paragraphs)
        elif filename.endswith(".txt"):
            text = (await file.read()).decode("utf-8", "ignore")
        else:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported file format")
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - runtime parse errors
        logger.exception("Failed to load file: %s", exc)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file") from exc

    return text

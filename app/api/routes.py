"""FastAPI routes for document ingestion."""
from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, HTTPException, UploadFile

from app.tasks.orchestrator import process_legal_document

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/documents")
async def upload_document(document: UploadFile, extraction_mode: str = "all") -> dict[str, str]:
    """Receive a document upload and enqueue the extraction task."""
    if extraction_mode not in {"all", "ner-only"}:
        raise HTTPException(status_code=400, detail="Invalid extraction_mode. Use 'all' or 'ner-only'.")
    document_id = str(uuid4())
    upload_path = Path("/tmp") / f"{document_id}-{document.filename}"
    content = await document.read()
    upload_path.write_bytes(content)
    task = process_legal_document.delay(document_id, str(upload_path), extraction_mode)
    logger.info(
        "document_upload enqueued task_id=%s document_id=%s mode=%s",
        task.id,
        document_id,
        extraction_mode,
    )
    return {"task_id": task.id, "document_id": document_id}

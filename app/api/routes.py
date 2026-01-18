"""FastAPI routes for document ingestion."""
from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, UploadFile

from app.tasks.orchestrator import process_legal_document

router = APIRouter()


@router.post("/documents")
async def upload_document(document: UploadFile) -> dict[str, str]:
    document_id = str(uuid4())
    upload_path = Path("/tmp") / f"{document_id}-{document.filename}"
    content = await document.read()
    upload_path.write_bytes(content)
    task = process_legal_document.delay(document_id, str(upload_path))
    return {"task_id": task.id, "document_id": document_id}

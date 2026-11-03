import base64
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
import httpx
from sqlalchemy.orm import Session

from src.app.api.deps import get_db
from src.app.core.exceptions import DocumentNotFoundError, FileValidationError
from src.app.models.document import Chunk, Document
from src.app.models.enums import DocumentStatus, WorkflowStatus
from src.app.models.workflow import WorkflowExecution
from src.app.schemas.document import (
    ChunkResponse,
    DocumentDetailResponse,
    DocumentResponse,
    IngestionTriggerResponse,
    WebhookIngestRequest,
)
from src.app.services.ingestion.pipeline import IngestionPipeline

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=IngestionTriggerResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> IngestionTriggerResponse:
    """Accepts document upload, validates, extracts text/tables/metadata, and saves chunks."""
    file_bytes = await file.read()
    filename = file.filename or "uploaded_file"

    pipeline = IngestionPipeline(db)
    doc, job, is_duplicate = pipeline.process_file(
        filename=filename,
        file_bytes=file_bytes,
        custom_metadata={"content_type": file.content_type},
    )

    message = "Existing duplicate document reused." if is_duplicate else "Document successfully parsed and ingested."

    return IngestionTriggerResponse(
        document=DocumentResponse.model_validate(doc),
        job_id=job.id,
        is_duplicate=is_duplicate,
        message=message,
    )


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    status_filter: Optional[DocumentStatus] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> List[DocumentResponse]:
    """Lists documents with pagination and optional status filter."""
    query = db.query(Document)
    if status_filter:
        query = query.filter(Document.status == status_filter)
    docs = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()
    return [DocumentResponse.model_validate(d) for d in docs]


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
) -> DocumentDetailResponse:
    """Retrieves document details with version history and chunk count."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise DocumentNotFoundError(document_id)

    chunk_count = db.query(Chunk).filter(Chunk.document_id == document_id).count()

    response = DocumentDetailResponse.model_validate(doc)
    response.chunk_count = chunk_count
    return response


@router.get("/{document_id}/chunks", response_model=List[ChunkResponse])
def get_document_chunks(
    document_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> List[ChunkResponse]:
    """Retrieves extracted chunks for a given document."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise DocumentNotFoundError(document_id)

    chunks = (
        db.query(Chunk)
        .filter(Chunk.document_id == document_id)
        .order_by(Chunk.chunk_index.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [ChunkResponse.model_validate(c) for c in chunks]


@router.post("/webhook-ingest", response_model=IngestionTriggerResponse, status_code=status.HTTP_201_CREATED)
async def webhook_ingest_document(
    payload: WebhookIngestRequest,
    db: Session = Depends(get_db),
) -> IngestionTriggerResponse:
    """Webhook-compatible ingestion endpoint accepting base64 or URL payloads from automation tools like n8n."""
    file_bytes: Optional[bytes] = None

    # Step 1: Extract binary data from Base64 or download from URL
    if payload.file_base64:
        try:
            file_bytes = base64.b64decode(payload.file_base64)
        except Exception as exc:
            raise FileValidationError(
                f"Failed to decode base64 file data: {exc}",
                details={"filename": payload.filename},
            )
    elif payload.file_url:
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                res = await client.get(payload.file_url)
                if res.status_code != 200:
                    raise FileValidationError(
                        f"Failed to download file from URL (status {res.status_code})",
                        details={"url": payload.file_url, "status_code": res.status_code},
                    )
                file_bytes = res.content
        except Exception as exc:
            if isinstance(exc, FileValidationError):
                raise exc
            raise FileValidationError(
                f"Network error downloading file from URL: {exc}",
                details={"url": payload.file_url, "error": str(exc)},
            )
    else:
        raise FileValidationError(
            "Either 'file_base64' or 'file_url' must be provided in the request payload.",
            details={"filename": payload.filename},
        )

    # Step 2: Track workflow execution if requested
    wf_exec: Optional[WorkflowExecution] = None
    if payload.workflow_id:
        wf_exec = WorkflowExecution(
            id=payload.workflow_id,
            workflow_type="n8n_document_ingestion",
            status=WorkflowStatus.RUNNING,
            input_payload={"filename": payload.filename, "metadata": payload.metadata},
            started_at=datetime.now(timezone.utc),
        )
        db.merge(wf_exec)
        db.commit()

    # Step 3: Run reusable ingestion pipeline
    try:
        pipeline = IngestionPipeline(db)
        doc, job, is_duplicate = pipeline.process_file(
            filename=payload.filename,
            file_bytes=file_bytes,
            custom_metadata=payload.metadata,
        )

        if wf_exec:
            wf_exec.status = WorkflowStatus.COMPLETED
            wf_exec.output_payload = {
                "document_id": doc.id,
                "job_id": job.id,
                "is_duplicate": is_duplicate,
            }
            wf_exec.completed_at = datetime.now(timezone.utc)
            db.commit()

        message = (
            "Existing duplicate document reused."
            if is_duplicate
            else "Document successfully ingested via automation webhook."
        )

        return IngestionTriggerResponse(
            document=DocumentResponse.model_validate(doc),
            job_id=job.id,
            is_duplicate=is_duplicate,
            message=message,
        )

    except Exception as exc:
        if wf_exec:
            wf_exec.status = WorkflowStatus.FAILED
            wf_exec.error_message = str(exc)
            wf_exec.completed_at = datetime.now(timezone.utc)
            db.commit()
        raise exc


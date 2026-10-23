from typing import List, Optional
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from src.app.api.deps import get_db
from src.app.core.exceptions import DocumentNotFoundError
from src.app.models.document import Chunk, Document
from src.app.models.enums import DocumentStatus
from src.app.schemas.document import (
    ChunkResponse,
    DocumentDetailResponse,
    DocumentResponse,
    IngestionTriggerResponse,
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

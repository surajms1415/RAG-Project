import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from src.app.core.exceptions import (
    AppException,
    CorruptFileError,
    FileValidationError,
    IngestionJobError,
)
from src.app.models.document import Chunk, Document, DocumentVersion
from src.app.models.enums import DocumentStatus, FileType, JobStatus
from src.app.models.job import IngestionJob
from src.app.services.ingestion.detector import (
    quick_integrity_check,
    validate_file_metadata,
)
from src.app.services.ingestion.hasher import (
    calculate_content_hash,
    find_document_by_hash,
)
from src.app.services.ingestion.parsers import get_parser_for_type
from src.app.services.rag.embeddings import get_embedding_service

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Orchestrates document ingestion, validation, hashing, deduplication, parsing, and database persistence."""

    def __init__(self, db: Session):
        self.db = db

    def process_file(
        self,
        filename: str,
        file_bytes: bytes,
        custom_metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Document, IngestionJob, bool]:
        """Ingests a file through validation, parsing, chunking, and database persistence.

        Returns:
            Tuple of (Document, IngestionJob, is_duplicate)
        """
        file_size = len(file_bytes)
        logger.info(f"Starting ingestion for file: '{filename}' ({file_size} bytes)")

        # Step 1: Pre-validation of metadata and size
        _, file_type = validate_file_metadata(filename=filename, file_size=file_size)

        # Step 2: Content Hash calculation for deduplication
        content_hash = calculate_content_hash(file_bytes)

        # Step 3: Check for duplicate content
        existing_doc = find_document_by_hash(self.db, content_hash)
        if existing_doc and existing_doc.status == DocumentStatus.COMPLETED:
            logger.info(
                f"Duplicate file detected (hash: {content_hash}). Reusing existing document ID: {existing_doc.id}"
            )
            latest_job = (
                self.db.query(IngestionJob)
                .filter(IngestionJob.document_id == existing_doc.id)
                .order_by(IngestionJob.created_at.desc())
                .first()
            )
            return existing_doc, latest_job, True

        # Step 4: Quick structural integrity check (headers, zip check)
        quick_integrity_check(file_bytes=file_bytes, file_type=file_type)

        # Step 5: Initialize Document record
        doc_id = str(uuid.uuid4())
        doc = Document(
            id=doc_id,
            title=filename,
            file_type=file_type,
            source_uri=filename,
            file_size_bytes=file_size,
            content_hash=content_hash,
            status=DocumentStatus.PROCESSING,
            doc_metadata=custom_metadata or {},
        )
        self.db.add(doc)

        # Initialize IngestionJob
        job_id = str(uuid.uuid4())
        job = IngestionJob(
            id=job_id,
            document_id=doc_id,
            status=JobStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
            retry_count=0,
            is_retryable=False,
        )
        self.db.add(job)
        self.db.commit()

        # Step 6: Parse file
        try:
            parser = get_parser_for_type(file_type)
            extraction = parser.extract(file_bytes=file_bytes, filename=filename)

            # Step 7: Persist DocumentVersion
            version_id = str(uuid.uuid4())
            version = DocumentVersion(
                id=version_id,
                document_id=doc_id,
                version_number=1,
                content_hash=content_hash,
                file_size_bytes=file_size,
                page_count=extraction.page_count,
                extracted_metadata=extraction.metadata,
            )
            self.db.add(version)

            # Generate real embeddings for all chunks
            chunk_texts = [c.content for c in extraction.chunks]
            try:
                embedding_service = get_embedding_service()
                chunk_embeddings = embedding_service.embed_batch(chunk_texts)
            except Exception as e:
                logger.error(f"Failed to generate embeddings during ingestion: {e}", exc_info=True)
                chunk_embeddings = [None] * len(chunk_texts)

            # Persist Chunks with embeddings and metadata
            for i, chunk_data in enumerate(extraction.chunks):
                meta = dict(chunk_data.metadata)
                meta["filename"] = filename
                meta["source_uri"] = filename
                meta["file_type"] = file_type.value

                emb = chunk_embeddings[i] if i < len(chunk_embeddings) else None

                chunk = Chunk(
                    id=str(uuid.uuid4()),
                    document_id=doc_id,
                    document_version_id=version_id,
                    chunk_index=chunk_data.chunk_index,
                    content=chunk_data.content,
                    section_title=chunk_data.section_title,
                    page_number=chunk_data.page_number,
                    token_count=chunk_data.token_count,
                    chunk_metadata=meta,
                    embedding=emb,
                )
                self.db.add(chunk)

            # Mark Document and Job as COMPLETED
            doc.status = DocumentStatus.COMPLETED
            doc.current_version_id = version_id

            job.version_id = version_id
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now(timezone.utc)

            self.db.commit()
            self.db.refresh(doc)
            self.db.refresh(job)

            logger.info(
                f"Ingestion successful for document '{doc.id}'. Extracted {len(extraction.chunks)} chunks."
            )
            return doc, job, False

        except (CorruptFileError, FileValidationError) as exc:
            self.db.rollback()
            logger.warning(f"Ingestion failed with validation/corrupt error: {exc.message}")
            self._record_failure(
                doc_id=doc_id,
                job_id=job_id,
                error_message=exc.message,
                error_details=exc.details,
                is_retryable=False,
            )
            raise exc

        except Exception as exc:
            self.db.rollback()
            logger.error(f"Unexpected error during ingestion: {exc}", exc_info=True)
            self._record_failure(
                doc_id=doc_id,
                job_id=job_id,
                error_message=str(exc),
                error_details={"exception_type": exc.__class__.__name__},
                is_retryable=True,
            )
            raise IngestionJobError(
                f"Ingestion failed unexpectedly: {exc}",
                is_retryable=True,
                details={"doc_id": doc_id, "error": str(exc)},
            )

    def _record_failure(
        self,
        doc_id: str,
        job_id: str,
        error_message: str,
        error_details: Dict[str, Any],
        is_retryable: bool,
    ) -> None:
        """Records failure on Document and IngestionJob, committing safely without corrupting data."""
        try:
            doc = self.db.query(Document).filter(Document.id == doc_id).first()
            if doc:
                doc.status = DocumentStatus.FAILED

            job = self.db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
            if job:
                job.status = JobStatus.FAILED
                job.error_message = error_message
                job.error_details = error_details
                job.is_retryable = is_retryable
                job.completed_at = datetime.now(timezone.utc)

            self.db.commit()
        except Exception as e:
            logger.critical(f"Failed to record ingestion failure: {e}", exc_info=True)
            self.db.rollback()

import io
import pytest
from fastapi import status
from src.app.core.exceptions import CorruptFileError, FileValidationError
from src.app.models.document import Chunk, Document, DocumentVersion
from src.app.models.enums import DocumentStatus, JobStatus
from src.app.models.job import IngestionJob
from src.app.services.ingestion.pipeline import IngestionPipeline


def test_pdf_ingestion_success(db_session, sample_pdf_bytes):
    """Acceptance test: Supported PDF file is parsed, extracting text, tables, metadata, and chunks."""
    pipeline = IngestionPipeline(db_session)
    doc, job, is_dup = pipeline.process_file("financial_report.pdf", sample_pdf_bytes)

    assert is_dup is False
    assert doc.status == DocumentStatus.COMPLETED
    assert job.status == JobStatus.COMPLETED
    assert doc.current_version_id is not None

    # Verify version
    version = db_session.query(DocumentVersion).filter(DocumentVersion.document_id == doc.id).first()
    assert version is not None
    assert version.page_count >= 1
    assert "Financial Report 2026" in version.extracted_metadata.get("title", "")

    # Verify chunks
    chunks = db_session.query(Chunk).filter(Chunk.document_id == doc.id).all()
    assert len(chunks) > 0

    chunk_contents = " ".join([c.content for c in chunks])
    assert "Financial Report 2026" in chunk_contents
    assert "Revenue grew by 24%" in chunk_contents

    # Verify page preservation
    assert any(c.page_number is not None for c in chunks)


def test_docx_ingestion_success(db_session, sample_docx_bytes):
    """Acceptance test: Supported DOCX file is parsed with headings, tables, and metadata."""
    pipeline = IngestionPipeline(db_session)
    doc, job, is_dup = pipeline.process_file("architecture.docx", sample_docx_bytes)

    assert doc.status == DocumentStatus.COMPLETED
    assert job.status == JobStatus.COMPLETED

    version = db_session.query(DocumentVersion).filter(DocumentVersion.document_id == doc.id).first()
    assert version.extracted_metadata["author"] == "System Architect"

    chunks = db_session.query(Chunk).filter(Chunk.document_id == doc.id).all()
    assert len(chunks) >= 2

    # Verify section preservation
    sections = [c.section_title for c in chunks if c.section_title]
    assert "Architecture Overview" in sections or "Component Specifications" in sections

    # Verify table extraction in markdown
    chunk_contents = " ".join([c.content for c in chunks])
    assert "Parser Engine" in chunk_contents


def test_pptx_ingestion_success(db_session, sample_pptx_bytes):
    """Acceptance test: Supported PPTX file is parsed with slides, titles, and text."""
    pipeline = IngestionPipeline(db_session)
    doc, job, is_dup = pipeline.process_file("ai_roadmap.pptx", sample_pptx_bytes)

    assert doc.status == DocumentStatus.COMPLETED
    assert job.status == JobStatus.COMPLETED

    chunks = db_session.query(Chunk).filter(Chunk.document_id == doc.id).all()
    assert len(chunks) >= 2

    chunk_contents = " ".join([c.content for c in chunks])
    assert "AI Roadmap 2026" in chunk_contents
    assert "Core Milestones" in chunk_contents
    assert "Phase 1: Ingestion Pipeline" in chunk_contents


def test_csv_ingestion_success(db_session, sample_csv_bytes):
    """Acceptance test: Supported CSV file is parsed with schema overview, tables, and row batches."""
    pipeline = IngestionPipeline(db_session)
    doc, job, is_dup = pipeline.process_file("infrastructure_costs.csv", sample_csv_bytes)

    assert doc.status == DocumentStatus.COMPLETED
    assert job.status == JobStatus.COMPLETED

    version = db_session.query(DocumentVersion).filter(DocumentVersion.document_id == doc.id).first()
    meta = version.extracted_metadata
    assert meta["row_count"] == 3
    assert "category" in meta["columns"]

    chunks = db_session.query(Chunk).filter(Chunk.document_id == doc.id).all()
    assert len(chunks) >= 2

    overview_chunk = chunks[0]
    assert "Dataset Summary" in overview_chunk.content

    table_chunk = chunks[1]
    assert "Compute" in table_chunk.content


def test_duplicate_upload_detection(db_session, sample_pdf_bytes):
    """Acceptance test: Content hashes detect duplicate uploads and reuse existing records."""
    pipeline = IngestionPipeline(db_session)

    # First upload
    doc1, job1, is_dup1 = pipeline.process_file("report.pdf", sample_pdf_bytes)
    assert is_dup1 is False

    # Second upload with identical bytes (even if different filename)
    doc2, job2, is_dup2 = pipeline.process_file("report_renamed.pdf", sample_pdf_bytes)
    assert is_dup2 is True
    assert doc1.id == doc2.id
    assert doc2.content_hash == doc1.content_hash

    # Ensure duplicate did not insert duplicate chunks
    total_docs = db_session.query(Document).count()
    assert total_docs == 1


def test_corrupt_file_graceful_failure(db_session):
    """Acceptance test: Corrupt files fail gracefully without corrupting database state or leaving orphan chunks."""
    pipeline = IngestionPipeline(db_session)

    corrupt_pdf_bytes = b"%PDF-1.4 garbage corrupt byte stream not a valid pdf document"

    with pytest.raises(CorruptFileError):
        pipeline.process_file("corrupt.pdf", corrupt_pdf_bytes)

    # Verify database state was NOT corrupted
    failed_doc = db_session.query(Document).filter(Document.title == "corrupt.pdf").first()
    assert failed_doc is not None
    assert failed_doc.status == DocumentStatus.FAILED

    failed_job = db_session.query(IngestionJob).filter(IngestionJob.document_id == failed_doc.id).first()
    assert failed_job is not None
    assert failed_job.status == JobStatus.FAILED
    assert failed_job.is_retryable is False
    assert failed_job.error_message is not None

    # No orphan chunks or versions were persisted
    chunks = db_session.query(Chunk).filter(Chunk.document_id == failed_doc.id).all()
    assert len(chunks) == 0

    versions = db_session.query(DocumentVersion).filter(DocumentVersion.document_id == failed_doc.id).all()
    assert len(versions) == 0


def test_empty_file_validation_error(db_session):
    """Acceptance test: Empty files (0 bytes) are rejected cleanly."""
    pipeline = IngestionPipeline(db_session)

    with pytest.raises(FileValidationError) as exc_info:
        pipeline.process_file("empty.pdf", b"")

    assert "empty" in str(exc_info.value).lower()


def test_unsupported_extension_error(db_session):
    """Acceptance test: Unsupported file formats are rejected with informative error."""
    pipeline = IngestionPipeline(db_session)

    with pytest.raises(FileValidationError) as exc_info:
        pipeline.process_file("script.exe", b"binarycontent")

    assert "unsupported file extension" in str(exc_info.value).lower()


def test_api_upload_endpoint(client, sample_csv_bytes):
    """Acceptance test: Full API upload, document retrieval, and chunk retrieval."""
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("metrics.csv", sample_csv_bytes, "text/csv")},
    )
    assert response.status_code == status.HTTP_201_CREATED

    res_data = response.json()
    assert "document" in res_data
    doc_id = res_data["document"]["id"]
    assert res_data["document"]["status"] == "COMPLETED"

    # Fetch document detail
    doc_resp = client.get(f"/api/v1/documents/{doc_id}")
    assert doc_resp.status_code == status.HTTP_200_OK
    assert doc_resp.json()["chunk_count"] > 0

    # Fetch document chunks
    chunks_resp = client.get(f"/api/v1/documents/{doc_id}/chunks")
    assert chunks_resp.status_code == status.HTTP_200_OK
    assert len(chunks_resp.json()) > 0

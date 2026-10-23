import pytest
from unittest.mock import patch
from fastapi import status
from src.app.core.config import Settings
from src.app.core.database import check_database_health, run_migrations
from src.app.models.document import Document, DocumentVersion, Chunk
from src.app.models.job import IngestionJob
from src.app.models.conversation import Conversation, Message
from src.app.models.workflow import WorkflowExecution
from src.app.models.enums import DocumentStatus, FileType, JobStatus, MessageRole, WorkflowStatus


def test_configuration_validation():
    """Validates configuration startup validation and environment parsing."""
    # Test valid configuration
    s = Settings(
        DATABASE_URL="sqlite:///./test.db",
        APP_ENV="test",
        MAX_UPLOAD_SIZE_BYTES=10000000,
    )
    assert s.DATABASE_URL == "sqlite:///./test.db"
    assert s.APP_ENV == "test"
    assert ".pdf" in s.ALLOWED_EXTENSIONS

    # Test automatic normalization of postgres:// to postgresql+psycopg://
    s2 = Settings(DATABASE_URL="postgres://user:pass@localhost:5432/db")
    assert s2.DATABASE_URL == "postgresql+psycopg://user:pass@localhost:5432/db"

    # Test invalid empty database URL
    with pytest.raises(Exception):
        Settings(DATABASE_URL="")


def test_health_check_healthy(client):
    """Acceptance test: Application starts and reports healthy dependency status."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data["dependencies"]
    assert data["dependencies"]["database"]["status"] == "up"
    assert data["dependencies"]["database"]["error"] is None
    assert isinstance(data["dependencies"]["database"]["latency_ms"], (int, float))


def test_health_check_dependency_failure(client):
    """Acceptance test: Reports dependency failures clearly with 503 Service Unavailable."""
    with patch("src.app.api.routes.health.check_database_health") as mock_check:
        mock_check.return_value = {
            "status": "down",
            "latency_ms": 12.5,
            "dialect": "postgresql",
            "error": "Connection refused: could not connect to server at localhost:5432",
        }

        response = client.get("/health")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["dependencies"]["database"]["status"] == "down"
        assert "Connection refused" in data["dependencies"]["database"]["error"]


def test_data_models_and_stable_ids(db_session):
    """Tests all 7 required tables, UUID primary keys, and timestamp generation."""
    # 1. Document
    doc = Document(
        title="Sample Document",
        file_type=FileType.PDF,
        source_uri="sample.pdf",
        file_size_bytes=1024,
        content_hash="abc123hash",
        status=DocumentStatus.PENDING,
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    assert doc.id is not None
    assert len(doc.id) == 36  # Valid UUID string format
    assert doc.created_at is not None
    assert doc.updated_at is not None
    assert doc.status == DocumentStatus.PENDING

    # 2. Document Version
    version = DocumentVersion(
        document_id=doc.id,
        version_number=1,
        content_hash="abc123hash",
        file_size_bytes=1024,
        page_count=2,
    )
    db_session.add(version)
    db_session.commit()
    db_session.refresh(version)

    assert version.id is not None
    assert version.document_id == doc.id

    # 3. Chunk
    chunk = Chunk(
        document_id=doc.id,
        document_version_id=version.id,
        chunk_index=0,
        content="This is the first chunk.",
        section_title="Intro",
        page_number=1,
    )
    db_session.add(chunk)
    db_session.commit()
    db_session.refresh(chunk)

    assert chunk.id is not None
    assert chunk.chunk_index == 0

    # 4. Ingestion Job
    job = IngestionJob(
        document_id=doc.id,
        version_id=version.id,
        status=JobStatus.QUEUED,
        is_retryable=True,
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    assert job.id is not None
    assert job.status == JobStatus.QUEUED
    assert job.is_retryable is True

    # 5. Conversation
    conv = Conversation(title="Analysis Session")
    db_session.add(conv)
    db_session.commit()
    db_session.refresh(conv)

    assert conv.id is not None
    assert conv.title == "Analysis Session"

    # 6. Message
    msg = Message(
        conversation_id=conv.id,
        role=MessageRole.USER,
        content="What was the Q2 revenue?",
    )
    db_session.add(msg)
    db_session.commit()
    db_session.refresh(msg)

    assert msg.id is not None
    assert msg.conversation_id == conv.id
    assert msg.role == MessageRole.USER

    # 7. Workflow Execution
    wf = WorkflowExecution(
        workflow_type="document_ingestion",
        status=WorkflowStatus.RUNNING,
        input_payload={"doc_id": doc.id},
    )
    db_session.add(wf)
    db_session.commit()
    db_session.refresh(wf)

    assert wf.id is not None
    assert wf.workflow_type == "document_ingestion"
    assert wf.status == WorkflowStatus.RUNNING


def test_migrations_runner():
    """Acceptance test: Programmatic database migration runner execution."""
    success = run_migrations()
    assert success is True

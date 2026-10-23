from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    Text,
    ForeignKey,
    JSON,
    DateTime,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from src.app.models.base import TimeStampedModel
from src.app.models.enums import JobStatus


class IngestionJob(TimeStampedModel):
    """Tracks document processing, lifecycle states, failures, and retries."""

    __tablename__ = "ingestion_jobs"

    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_id = Column(String(36), ForeignKey("document_versions.id", ondelete="SET NULL"), nullable=True)
    status = Column(
        SQLEnum(JobStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=JobStatus.QUEUED,
        index=True,
    )
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True, default=dict)
    is_retryable = Column(Boolean, nullable=False, default=True)
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    document = relationship("Document", back_populates="jobs")

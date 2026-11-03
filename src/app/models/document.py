from sqlalchemy import (
    Column,
    String,
    Integer,
    BigInteger,
    Text,
    ForeignKey,
    JSON,
    DateTime,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from src.app.models.base import TimeStampedModel, generate_uuid, utc_now
from src.app.models.enums import DocumentStatus, FileType


class Document(TimeStampedModel):
    """Represents a managed document in the system."""

    __tablename__ = "documents"

    title = Column(String(255), nullable=False)
    file_type = Column(SQLEnum(FileType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    source_uri = Column(String(1024), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False, default=0)
    content_hash = Column(String(64), nullable=False, index=True)
    status = Column(
        SQLEnum(DocumentStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=DocumentStatus.PENDING,
        index=True,
    )
    current_version_id = Column(String(36), nullable=True)
    doc_metadata = Column(JSON, nullable=True, default=dict)

    # Relationships
    versions = relationship(
        "DocumentVersion",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentVersion.version_number.desc()",
    )
    chunks = relationship(
        "Chunk",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    jobs = relationship(
        "IngestionJob",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="IngestionJob.created_at.desc()",
    )

    @property
    def filename(self) -> str:
        return self.title or self.source_uri

    @property
    def chunk_count(self) -> int:
        return len(self.chunks) if self.chunks else 0


class DocumentVersion(TimeStampedModel):
    """Represents a specific version of a document."""

    __tablename__ = "document_versions"

    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False, default=1)
    content_hash = Column(String(64), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    page_count = Column(Integer, nullable=True)
    extracted_metadata = Column(JSON, nullable=True, default=dict)

    # Relationships
    document = relationship("Document", back_populates="versions")
    chunks = relationship("Chunk", back_populates="version", cascade="all, delete-orphan")


class Chunk(TimeStampedModel):
    """Represents a normalized semantic text chunk from a document version."""

    __tablename__ = "chunks"

    document_id = Column(String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    document_version_id = Column(
        String(36), ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    section_title = Column(String(255), nullable=True)
    page_number = Column(Integer, nullable=True)
    token_count = Column(Integer, nullable=True)
    chunk_metadata = Column(JSON, nullable=True, default=dict)
    embedding = Column(JSON, nullable=True)

    # Relationships
    document = relationship("Document", back_populates="chunks")
    version = relationship("DocumentVersion", back_populates="chunks")

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from src.app.models.enums import DocumentStatus, FileType


class ChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    chunk_index: int
    content: str
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    token_count: Optional[int] = None
    chunk_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class DocumentVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    version_number: int
    content_hash: str
    file_size_bytes: int
    page_count: Optional[int] = None
    extracted_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    file_type: FileType
    source_uri: str
    file_size_bytes: int
    content_hash: str
    status: DocumentStatus
    current_version_id: Optional[str] = None
    doc_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class DocumentDetailResponse(DocumentResponse):
    versions: List[DocumentVersionResponse] = Field(default_factory=list)
    chunk_count: int = 0


class IngestionTriggerResponse(BaseModel):
    document: DocumentResponse
    job_id: str
    is_duplicate: bool = False
    message: str

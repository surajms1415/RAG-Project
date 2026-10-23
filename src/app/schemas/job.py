from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field
from src.app.models.enums import JobStatus


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    version_id: Optional[str] = None
    status: JobStatus
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = Field(default_factory=dict)
    is_retryable: bool
    retry_count: int
    max_retries: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

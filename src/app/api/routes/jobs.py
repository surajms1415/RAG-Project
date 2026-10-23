from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.app.api.deps import get_db
from src.app.models.job import IngestionJob
from src.app.schemas.job import JobResponse

router = APIRouter(prefix="/jobs", tags=["Ingestion Jobs"])


@router.get("/{job_id}", response_model=JobResponse)
def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
) -> JobResponse:
    """Retrieves ingestion job execution status, failure reasons, and retryability."""
    job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found",
        )
    return JobResponse.model_validate(job)

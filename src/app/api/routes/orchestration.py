from typing import Optional
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.app.api.deps import get_db
from src.app.services.orchestration.router import (
    OrchestratorService,
    QueryRoute,
    UnifiedQueryResponse,
)

router = APIRouter(tags=["Unified Query Routing"])


class UnifiedQueryRequest(BaseModel):
    question: str = Field(..., min_length=2, description="Inquiry to route to RAG or Analytics.")
    route: Optional[QueryRoute] = Field(
        default=None,
        description="Optional forced route ('document_rag', 'structured_analytics', 'combined'). Auto-classified if omitted.",
    )
    route_override: Optional[QueryRoute] = Field(
        default=None,
        description="Alias for route.",
    )
    document_id: Optional[str] = Field(default=None, description="Optional document filter for RAG.")
    max_rows: Optional[int] = Field(default=50, ge=1, le=500, description="Max rows for analytics queries.")


@router.post("/query", response_model=UnifiedQueryResponse, status_code=status.HTTP_200_OK)
def unified_query(
    payload: UnifiedQueryRequest,
    db: Session = Depends(get_db),
) -> UnifiedQueryResponse:
    """Unified query router that intelligently routes questions to Document RAG, SQL Analytics, or Combined synthesis."""
    orchestrator = OrchestratorService(db)
    result = orchestrator.route_and_execute(
        question=payload.question,
        preferred_route=payload.route or payload.route_override,
        document_id=payload.document_id,
        max_rows=payload.max_rows or 50,
    )
    return result

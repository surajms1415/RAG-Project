from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.app.api.deps import get_db
from src.app.core.database import engine
from src.app.schemas.analytics import (
    AnalyticsQueryRequest,
    AnalyticsQueryResponse,
    SchemaOverviewResponse,
)
from src.app.services.analytics.analytics_service import BusinessAnalyticsService
from src.app.services.analytics.schema_inspector import (
    SCHEMA_DOCUMENTATION,
    get_approved_tables,
)

router = APIRouter(prefix="/analytics", tags=["Business Data Analytics"])


@router.post("/query", response_model=AnalyticsQueryResponse, status_code=status.HTTP_200_OK)
def query_business_analytics(
    payload: AnalyticsQueryRequest,
    db: Session = Depends(get_db),
) -> AnalyticsQueryResponse:
    """Translates a natural language business question into validated read-only SQL, executes it, and returns results with insights."""
    service = BusinessAnalyticsService(db)
    result = service.query(
        question=payload.question,
        max_rows=payload.max_rows or 50,
    )
    return AnalyticsQueryResponse.model_validate(result)


@router.get("/schema", response_model=SchemaOverviewResponse)
def get_analytics_schema() -> SchemaOverviewResponse:
    """Returns approved analytics tables and schema context."""
    return SchemaOverviewResponse(
        dialect=engine.dialect.name,
        approved_tables=get_approved_tables(),
        schema_documentation=SCHEMA_DOCUMENTATION.strip(),
    )

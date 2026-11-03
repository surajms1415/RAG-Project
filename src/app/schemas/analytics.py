from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AnalyticsQueryRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    question: str = Field(..., min_length=2, description="Natural language question about business metrics, sales, or customers.")
    max_rows: Optional[int] = Field(default=50, ge=1, le=500, description="Max rows to return.")


class AnalyticsQueryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    question: str
    sql_query: str
    generated_sql: Optional[str] = None
    explanation: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    data: Optional[List[Dict[str, Any]]] = None
    row_count: int
    summary: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float
    is_safe: bool = True

    def model_post_init(self, __context: Any) -> None:
        if self.generated_sql is None:
            self.generated_sql = self.sql_query
        if self.data is None:
            self.data = self.rows


class SchemaOverviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    dialect: str
    approved_tables: List[str]
    schema_documentation: str

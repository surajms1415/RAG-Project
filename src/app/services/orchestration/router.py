import logging
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.app.core.config import get_settings
from src.app.services.analytics.analytics_service import BusinessAnalyticsService
from src.app.services.rag.qa_service import QAService

logger = logging.getLogger(__name__)
settings = get_settings()


class QueryRoute(str, Enum):
    DOCUMENT_RAG = "document_rag"
    STRUCTURED_ANALYTICS = "structured_analytics"
    COMBINED = "combined"


class UnifiedQueryResponse(BaseModel):
    question: str
    route_used: QueryRoute
    route_taken: Optional[QueryRoute] = None
    answer: str
    final_answer: Optional[str] = None
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    sql_query: Optional[str] = None
    generated_sql: Optional[str] = None
    structured_data: Optional[List[Dict[str, Any]]] = None
    data: Optional[List[Dict[str, Any]]] = None
    structured_summary: Optional[Dict[str, Any]] = None
    has_sufficient_evidence: bool = True
    rag_result: Optional[Dict[str, Any]] = None
    analytics_result: Optional[Dict[str, Any]] = None

    def model_post_init(self, __context: Any) -> None:
        if self.route_taken is None:
            self.route_taken = self.route_used
        if self.final_answer is None:
            self.final_answer = self.answer
        if self.generated_sql is None:
            self.generated_sql = self.sql_query
        if self.data is None:
            self.data = self.structured_data


ANALYTICS_KEYWORDS = {
    "order", "orders", "customer", "customers", "product", "products",
    "revenue", "sales", "inventory", "stock", "unit_price", "units sold",
    "total spent", "total sales", "total amount", "top selling", "highest revenue"
}

DOCUMENT_KEYWORDS = {
    "document", "documents", "pdf", "docx", "pptx", "slide", "slides",
    "architecture", "framework", "policy", "spec", "specification",
    "report", "roadmap", "milestone", "section"
}


def classify_query_intent(question: str) -> QueryRoute:
    """Classifies natural language user inquiry into RAG, SQL Analytics, or Combined routing."""
    q_tokens = set(question.lower().split())
    
    analytics_matches = any(kw in question.lower() for kw in ANALYTICS_KEYWORDS)
    document_matches = any(kw in question.lower() for kw in DOCUMENT_KEYWORDS)

    if analytics_matches and document_matches:
        return QueryRoute.COMBINED
    elif analytics_matches:
        return QueryRoute.STRUCTURED_ANALYTICS
    elif document_matches:
        return QueryRoute.DOCUMENT_RAG

    # Default heuristic: check if any database table entity mentioned
    return QueryRoute.DOCUMENT_RAG


class OrchestratorService:
    """Intelligently routes natural-language questions to Document RAG, SQL Analytics, or Combined synthesis."""

    def __init__(self, db: Session):
        self.db = db
        self.rag_service = QAService(db)
        self.analytics_service = BusinessAnalyticsService(db)

    def route_and_execute(
        self,
        question: str,
        preferred_route: Optional[QueryRoute] = None,
        document_id: Optional[str] = None,
        max_rows: int = 50,
    ) -> UnifiedQueryResponse:
        route = preferred_route or classify_query_intent(question)
        logger.info(f"Routing query '{question}' to target engine: {route.value}")

        if route == QueryRoute.STRUCTURED_ANALYTICS:
            analytics_res = self.analytics_service.query(question=question, max_rows=max_rows)
            analytics_dict = {
                "question": question,
                "sql_query": analytics_res.sql_query,
                "generated_sql": analytics_res.sql_query,
                "explanation": analytics_res.explanation,
                "columns": analytics_res.columns,
                "rows": analytics_res.rows,
                "data": analytics_res.rows,
                "row_count": analytics_res.row_count,
                "summary": analytics_res.summary,
                "execution_time_ms": analytics_res.execution_time_ms,
                "is_safe": True,
            }
            return UnifiedQueryResponse(
                question=question,
                route_used=route,
                answer=analytics_res.explanation,
                sql_query=analytics_res.sql_query,
                structured_data=analytics_res.rows,
                structured_summary=analytics_res.summary,
                has_sufficient_evidence=analytics_res.row_count > 0,
                analytics_result=analytics_dict,
            )

        elif route == QueryRoute.DOCUMENT_RAG:
            rag_res = self.rag_service.answer_question(question=question, document_id=document_id)
            rag_dict = {
                "question": question,
                "answer": rag_res.answer,
                "citations": [c.model_dump() for c in rag_res.citations],
                "has_sufficient_evidence": rag_res.has_sufficient_evidence,
            }
            return UnifiedQueryResponse(
                question=question,
                route_used=route,
                answer=rag_res.answer,
                citations=[c.model_dump() for c in rag_res.citations],
                has_sufficient_evidence=rag_res.has_sufficient_evidence,
                rag_result=rag_dict,
            )

        else:  # COMBINED
            rag_res = self.rag_service.answer_question(question=question, document_id=document_id)
            analytics_res = self.analytics_service.query(question=question, max_rows=max_rows)

            combined_answer = (
                f"### Document Evidence\n{rag_res.answer}\n\n"
                f"### Structured Business Analytics\n{analytics_res.explanation}"
            )
            analytics_dict = {
                "question": question,
                "sql_query": analytics_res.sql_query,
                "generated_sql": analytics_res.sql_query,
                "explanation": analytics_res.explanation,
                "columns": analytics_res.columns,
                "rows": analytics_res.rows,
                "data": analytics_res.rows,
                "row_count": analytics_res.row_count,
                "summary": analytics_res.summary,
                "execution_time_ms": analytics_res.execution_time_ms,
                "is_safe": True,
            }
            rag_dict = {
                "question": question,
                "answer": rag_res.answer,
                "citations": [c.model_dump() for c in rag_res.citations],
                "has_sufficient_evidence": rag_res.has_sufficient_evidence,
            }

            return UnifiedQueryResponse(
                question=question,
                route_used=route,
                answer=combined_answer,
                citations=[c.model_dump() for c in rag_res.citations],
                sql_query=analytics_res.sql_query,
                structured_data=analytics_res.rows,
                structured_summary=analytics_res.summary,
                has_sufficient_evidence=rag_res.has_sufficient_evidence or (analytics_res.row_count > 0),
                rag_result=rag_dict,
                analytics_result=analytics_dict,
            )

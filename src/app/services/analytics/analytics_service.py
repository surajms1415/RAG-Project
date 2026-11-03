import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.app.core.config import get_settings
from src.app.core.exceptions import LLMConfigurationError
from src.app.services.analytics.schema_inspector import get_analytics_schema_context
from src.app.services.analytics.sql_executor import execute_analytics_query
from src.app.services.analytics.sql_validator import validate_and_sanitize_sql

logger = logging.getLogger(__name__)
settings = get_settings()

SQL_GENERATION_SYSTEM_PROMPT = """You are a senior data analyst and SQL expert.
Your job is to generate a single read-only SQL query to answer the user's business question.

RULES:
1. Return ONLY the raw SQL query. Do not wrap in markdown quotes, backticks, or write explanations.
2. Only use the approved tables: 'customers', 'products', 'orders', 'order_items'.
3. Only write SELECT queries (or queries with CTE 'WITH'). No mutations or DDL.
4. Use standard SQL compatible with the provided dialect.
"""

EXPLANATION_SYSTEM_PROMPT = """You are a helpful business intelligence analyst.
Explain the SQL query results concisely in 1-3 business-friendly sentences.
Highlight key findings (e.g. top numbers, totals, or notable outliers).
Do not repeat raw table dumps; provide executive insights.
"""


class AnalyticsQueryResult(BaseModel):
    question: str
    sql_query: str
    explanation: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    row_count: int
    summary: Dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float


class BusinessAnalyticsService:
    """Orchestrates natural language to SQL translation, validation, execution, and insight generation."""

    def __init__(self, db: Session):
        self.db = db

    def query(
        self,
        question: str,
        max_rows: int = 50,
    ) -> AnalyticsQueryResult:
        logger.info(f"Processing natural language business analytics question: '{question}'")

        # 1. Generate SQL from question and schema
        sql_query = self._generate_sql(question)

        # 2. Validate and sanitize SQL query
        validated_sql = validate_and_sanitize_sql(sql_query, max_rows=max_rows)
        logger.info(f"Executing validated SQL: {validated_sql}")

        # 3. Execute query with Pandas processing
        execution_result = execute_analytics_query(
            db=self.db,
            validated_sql=validated_sql,
            timeout_seconds=settings.DATABASE_TIMEOUT_SECONDS,
        )

        # 4. Generate business explanation
        explanation = self._generate_explanation(
            question=question,
            sql_query=validated_sql,
            rows=execution_result["rows"],
            summary=execution_result["summary"],
        )

        return AnalyticsQueryResult(
            question=question,
            sql_query=validated_sql,
            explanation=explanation,
            columns=execution_result["columns"],
            rows=execution_result["rows"],
            row_count=execution_result["row_count"],
            summary=execution_result["summary"],
            execution_time_ms=execution_result["execution_time_ms"],
        )

    def _generate_sql(self, question: str) -> str:
        """Translates natural language to SQL using configured LLM or deterministic fallback."""
        schema_context = get_analytics_schema_context()

        # Check if using mock/offline provider
        if settings.LLM_PROVIDER.lower() == "mock" or not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.startswith("mock_"):
            return self._generate_mock_sql(question)

        try:
            from google import genai

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = (
                f"{SQL_GENERATION_SYSTEM_PROMPT}\n\n"
                f"{schema_context}\n\n"
                f"QUESTION: {question}\n\n"
                f"SQL QUERY:"
            )
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
            )
            return response.text.strip()

        except Exception as e:
            logger.warning(f"Gemini Text2SQL failed ({e}). Falling back to heuristic SQL mapper.")
            return self._generate_mock_sql(question)

    def _generate_mock_sql(self, question: str) -> str:
        """Deterministic SQL mapper for common business questions in test/offline environments."""
        q = question.lower()

        if "top" in q and ("product" in q or "revenue" in q or "sales" in q):
            return (
                "SELECT p.name AS product_name, p.category, SUM(oi.total_price) AS total_revenue "
                "FROM products p "
                "JOIN order_items oi ON p.id = oi.product_id "
                "GROUP BY p.id, p.name, p.category "
                "ORDER BY total_revenue DESC LIMIT 5"
            )

        if "customer" in q and ("order" in q or "count" in q or "total" in q or "spent" in q):
            return (
                "SELECT c.name AS customer_name, c.segment, COUNT(o.id) AS order_count, SUM(o.total_amount) AS total_spent "
                "FROM customers c "
                "JOIN orders o ON c.id = o.customer_id "
                "GROUP BY c.id, c.name, c.segment "
                "ORDER BY total_spent DESC LIMIT 10"
            )

        if "category" in q or "categories" in q:
            return (
                "SELECT p.category, COUNT(p.id) AS product_count, AVG(p.unit_price) AS avg_unit_price "
                "FROM products p "
                "GROUP BY p.category "
                "ORDER BY product_count DESC"
            )

        if "city" in q or "cities" in q or "location" in q:
            return (
                "SELECT shipping_city, COUNT(id) AS order_count, SUM(total_amount) AS total_sales "
                "FROM orders "
                "GROUP BY shipping_city "
                "ORDER BY total_sales DESC"
            )

        # Default fallback: recent completed orders
        return (
            "SELECT o.id AS order_id, c.name AS customer_name, o.order_date, o.status, o.total_amount "
            "FROM orders o "
            "JOIN customers c ON o.customer_id = c.id "
            "ORDER BY o.order_date DESC LIMIT 10"
        )

    def _generate_explanation(
        self,
        question: str,
        sql_query: str,
        rows: List[Dict[str, Any]],
        summary: Dict[str, Any],
    ) -> str:
        """Generates executive summary of the query findings."""
        if not rows:
            return "No matching business records were found for this query."

        row_count = len(rows)

        # In offline/mock mode or if no Gemini key, build clear summary from rows & metrics
        if settings.LLM_PROVIDER.lower() == "mock" or not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.startswith("mock_"):
            first_row = rows[0]
            first_val = list(first_row.values())[0]
            second_val = list(first_row.values())[-1] if len(first_row) > 1 else ""

            if "total_revenue" in first_row or "total_spent" in first_row or "total_sales" in first_row:
                metric_name = "total_revenue" if "total_revenue" in first_row else ("total_spent" if "total_spent" in first_row else "total_sales")
                return (
                    f"Retrieved {row_count} records. Top performer is '{first_val}' with "
                    f"${first_row[metric_name]:,.2f} in sales volume."
                )
            return f"Query successfully retrieved {row_count} business records matching '{question}'."

        # If live LLM is configured, request brief executive insight
        try:
            from google import genai

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = (
                f"{EXPLANATION_SYSTEM_PROMPT}\n\n"
                f"QUESTION: {question}\n"
                f"SQL: {sql_query}\n"
                f"SAMPLE DATA (first 5 rows): {rows[:5]}\n"
                f"SUMMARY METRICS: {summary}\n\n"
                f"EXECUTIVE EXPLANATION:"
            )
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
            )
            return response.text.strip()
        except Exception:
            return f"Query successfully retrieved {row_count} records for question '{question}'."

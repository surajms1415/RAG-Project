import logging
import time
from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.app.core.config import get_settings
from src.app.core.exceptions import AppException

logger = logging.getLogger(__name__)
settings = get_settings()


class QueryExecutionError(AppException):
    """Raised when SQL execution fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=500, details=details or {})


def execute_analytics_query(
    db: Session,
    validated_sql: str,
    timeout_seconds: Optional[int] = None,
) -> Dict[str, Any]:
    """Executes validated SQL and leverages Pandas for structured formatting and statistical summaries."""
    start_time = time.perf_counter()
    timeout = timeout_seconds or settings.DATABASE_TIMEOUT_SECONDS

    try:
        # Use Pandas for reliable tabular loading and data type conversions
        conn = db.connection()
        df = pd.read_sql_query(sql=text(validated_sql), con=conn)
        execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)

        row_count = len(df)
        columns = df.columns.tolist()

        # Generate practical summary metrics using Pandas
        summary_metrics: Dict[str, Any] = {
            "row_count": row_count,
            "execution_time_ms": execution_time_ms,
        }

        if not df.empty:
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            for col in numeric_cols:
                # Include total sum and mean for numerical aggregates (e.g. total revenue, quantity)
                summary_metrics[f"{col}_sum"] = round(float(df[col].sum()), 2)
                summary_metrics[f"{col}_avg"] = round(float(df[col].mean()), 2)

        # Convert dataframe rows to JSON-serializable list of dicts
        # Replace NaN with None
        clean_df = df.where(pd.notnull(df), None)
        records = clean_df.to_dict(orient="records")

        return {
            "sql": validated_sql,
            "columns": columns,
            "rows": records,
            "row_count": row_count,
            "summary": summary_metrics,
            "execution_time_ms": execution_time_ms,
        }

    except Exception as exc:
        logger.error(f"Failed to execute analytics query '{validated_sql}': {exc}", exc_info=True)
        raise QueryExecutionError(
            f"Query execution failed: {exc}",
            details={"sql": validated_sql, "error": str(exc)},
        )

import re
from typing import Set, Tuple
from src.app.core.exceptions import AppException
from src.app.services.analytics.schema_inspector import APPROVED_ANALYTICS_TABLES

FORBIDDEN_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "EXEC",
    "EXECUTE",
    "CREATE",
    "RENAME",
    "REPLACE",
    "MERGE",
    "GRANT",
    "REVOKE",
    "PRAGMA",
    "ATTACH",
    "DETACH",
    "INTO",
    "LOAD_EXTENSION",
}

FORBIDDEN_SYSTEM_PREFIXES = (
    "sqlite_",
    "pg_",
    "information_schema",
    "performance_schema",
    "alembic_",
)


class SQLSecurityError(AppException):
    """Raised when generated SQL violates safety constraints."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message=message, status_code=400, details=details or {})


def clean_sql_string(raw_sql: str) -> str:
    """Strips markdown code blocks, backticks, and extra whitespace."""
    sql = raw_sql.strip()
    if sql.startswith("```"):
        lines = sql.split("\n")
        # Remove opening and closing fence
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        sql = "\n".join(lines).strip()
    return sql.rstrip(";")


def validate_and_sanitize_sql(
    raw_sql: str,
    max_rows: int = 100,
) -> str:
    """Validates that query is strictly a safe read-only SELECT query against approved tables."""
    sql = clean_sql_string(raw_sql)

    if not sql:
        raise SQLSecurityError("Generated SQL is empty.")

    # 1. Multi-statement check
    # Check for unquoted semicolons
    cleaned_no_strings = re.sub(r"'[^']*'", "", sql)
    if ";" in cleaned_no_strings:
        raise SQLSecurityError("Multiple SQL statements are strictly prohibited.")

    # 2. Must start with SELECT or WITH
    first_word = sql.split()[0].upper()
    if first_word not in ("SELECT", "WITH"):
        raise SQLSecurityError(
            f"Only read-only SELECT queries are permitted. Found: '{first_word}'"
        )

    # 3. Check for mutating / forbidden keywords
    tokens = set(re.findall(r"\b[A-Za-z_]+\b", cleaned_no_strings.upper()))
    intersection = tokens.intersection(FORBIDDEN_KEYWORDS)
    if intersection:
        raise SQLSecurityError(
            f"Query contains forbidden keyword(s): {', '.join(sorted(intersection))}"
        )

    # 4. Check for system tables
    for forbidden_prefix in FORBIDDEN_SYSTEM_PREFIXES:
        if forbidden_prefix.lower() in sql.lower():
            raise SQLSecurityError(f"Access to system catalog table '{forbidden_prefix}' is denied.")

    # 5. Extract table names and ensure they are within approved tables
    # Match patterns like FROM table or JOIN table
    table_matches = re.findall(r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)", sql, re.IGNORECASE)
    referenced_tables = {t.lower() for t in table_matches}

    for table in referenced_tables:
        if table not in APPROVED_ANALYTICS_TABLES:
            raise SQLSecurityError(
                f"Unauthorized table '{table}'. Permitted analytics tables: {sorted(list(APPROVED_ANALYTICS_TABLES))}"
            )

    # 6. Enforce safe LIMIT clause
    limit_match = re.search(r"\bLIMIT\s+(\d+)", sql, re.IGNORECASE)
    if limit_match:
        current_limit = int(limit_match.group(1))
        if current_limit > max_rows:
            # Replace with maximum allowable limit
            sql = re.sub(r"\bLIMIT\s+\d+", f"LIMIT {max_rows}", sql, flags=re.IGNORECASE)
    else:
        sql = f"{sql} LIMIT {max_rows}"

    return sql

# Enterprise AI Document & Analytics Platform

An enterprise-grade document ingestion, hybrid RAG, and structured analytics platform built with FastAPI, SQLAlchemy, Alembic, and high-performance document extractors.

---

## Architecture Overview

```
                      ┌──────────────────────────────────────┐
                      │             Input Layer              │
                      │  API Uploads · Webhooks · Automation │
                      └──────────────────┬───────────────────┘
                                         │
                                         ▼
                      ┌──────────────────────────────────────┐
                      │            Python + FastAPI          │
                      │   Validation · Config · LifeCycle    │
                      └──────────┬────────────────┬──────────┘
                                 │                │
            ┌────────────────────┴───┐        ┌───┴────────────────────┐
            │   Document Ingestion   │        │  Structured Analytics  │
            │   PDF, DOCX, PPTX, CSV │        │  PostgreSQL/SQLAlchemy │
            └────────────────────────┘        └────────────────────────┘
```

---

## Modules Implemented

### 01. Foundation and Data Model
- **Configuration & Secrets**: Centralized Pydantic `BaseSettings` (`Settings` in `src/app/core/config.py`) loading secrets from environment variables with startup validation.
- **Structured Logging & Error Handling**: Global custom exception hierarchy (`AppException`, `FileValidationError`, `CorruptFileError`, `DatabaseConnectionError`, `IngestionJobError`) with standardized JSON error responses.
- **Database Connection & Pool**: SQLAlchemy session factory with PostgreSQL and SQLite support (`src/app/core/database.py`).
- **Data Models**:
  - `documents`: Stable UUIDv4 primary keys, file metadata, status enums, SHA-256 content hashes, UTC timestamps.
  - `document_versions`: Revision history, page counts, extracted metadata.
  - `chunks`: Extracted text chunks with breadcrumbs (`section_title`, `page_number`, token counts).
  - `ingestion_jobs`: Lifecycle tracking (`QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`), retryability (`is_retryable`), failure messages, and audit timestamps.
  - `conversations` & `messages`: Multi-turn conversation sessions and message turns with citations.
  - `workflow_executions`: Automation and workflow run tracking.
- **Alembic Database Migrations**: Versioned migration scripts in `alembic/versions/0001_initial_schema.py` and programmatic runner `run_migrations()`.
- **Health-Check Endpoint**: `GET /health` tests live database connectivity via `SELECT 1` and returns dependency status with latency or reports dependency failures clearly (HTTP 503).

### 02. Document Ingestion Pipeline
- **Reusable Parsers**:
  - **PDF (`PDFParser`)**: PyMuPDF-backed engine extracting page text, layout metadata, and native tables into Markdown.
  - **DOCX (`DOCXParser`)**: Extracts heading-based hierarchical sections and Markdown-formatted tables.
  - **PPTX (`PPTXParser`)**: Slide-by-slide extraction preserving slide titles, shape text, notes, and tables.
  - **CSV (`CSVParser`)**: Schema profiling, column summaries, and batch tabular chunking.
- **Pre-flight File Validation**:
  - Supported extensions (`.pdf`, `.docx`, `.pptx`, `.csv`).
  - Size limit checking (default 50MB, configurable via `MAX_UPLOAD_SIZE_BYTES`).
  - Empty file detection (0 bytes or blank text).
  - Magic byte and archive structure integrity validation before full parsing.
- **Text Normalization**: Unicode NFKC standardization, control character stripping, whitespace collapse, and metadata context prefixing (`[Section: ... | Page: ...]`).
- **Content Hashing & Deduplication**: SHA-256 fingerprinting checks existing completed documents and avoids redundant re-ingestion.
- **Job Status & Failure Tracking**: Failure recording without database corruption or orphaned chunks. Flags `is_retryable` based on error type (corrupted files flagged non-retryable).

---

## Quick Start

### 1. Setup Environment
```bash
cp .env.example .env
pip install -r requirements.txt
```

### 2. Apply Database Migrations
```bash
python -m alembic upgrade head
```

### 3. Run Test Suite
```bash
python -m pytest tests/ -v
```

### 4. Start Application
```bash
uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health-check endpoint testing database connectivity |
| `POST` | `/api/v1/documents/upload` | Ingests PDF, DOCX, PPTX, or CSV document |
| `GET` | `/api/v1/documents` | Lists all ingested documents |
| `GET` | `/api/v1/documents/{id}` | Retrieves document details and chunk counts |
| `GET` | `/api/v1/documents/{id}/chunks` | Retrieves extracted chunks with section/page info |
| `GET` | `/api/v1/jobs/{id}` | Retrieves ingestion job status and failure telemetry |
| `POST` | `/api/v1/rag/query` | Answers questions via similarity retrieval and grounded citations |

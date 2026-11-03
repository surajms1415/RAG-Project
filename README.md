# InsightFlow AI: Enterprise Document Intelligence & Business Analytics Platform

An enterprise-ready AI platform combining multi-format document ingestion, dense vector RAG (Retrieval-Augmented Generation), safe Text-to-SQL business analytics, automated n8n workflow integration, and a unified query orchestrator.

---

## 1. Project Overview & Architecture

InsightFlow AI bridges unstructured enterprise documents (PDF, DOCX, PPTX, CSV) and structured relational data (orders, sales, customers, products) through a centralized, grounded AI interface.

```
                              ┌───────────────────────────────────────────────┐
                              │                 Client Layers                 │
                              │  REST Clients · Webhooks · n8n Automation     │
                              └───────────────────────┬───────────────────────┘
                                                      │
                                                      ▼
                              ┌───────────────────────────────────────────────┐
                              │            FastAPI Gateway Layer              │
                              │    CORS · Config Validation · Global Errors   │
                              └───────┬──────────────────────┬─────────────┬──┘
                                      │                      │             │
                                      ▼                      ▼             ▼
       ┌────────────────────────────────┐  ┌──────────────────┐  ┌─────────────────────┐
       │   Document Ingestion Pipeline  │  │  Unified Query   │  │  Business Analytics │
       │  • PDF (PyMuPDF)               │  │   Orchestrator   │  │  • Text-to-SQL (LLM)│
       │  • DOCX / PPTX / CSV Parsers   │  │  • Document RAG  │  │  • AST SQL Validator│
       │  • Text Normalizer & Chunker   │  │  • SQL Analytics │  │  • Safe Execution   │
       │  • Content Hash Deduplication  │  │  • Hybrid Query  │  │  • Pandas Summaries │
       └──────────────┬─────────────────┘  └────────┬─────────┘  └──────────┬──────────┘
                      │                             │                       │
                      ▼                             ▼                       ▼
       ┌───────────────────────────────────────────────────────────────────────────────┐
       │                       Relational & Vector Storage Layer                       │
       │   PostgreSQL / SQLite · pgvector · Alembic Migrations · SQLAlchemy ORM        │
       │   • documents, chunks, ingestion_jobs, workflow_executions                    │
       │   • customers, products, orders, order_items                                  │
       └───────────────────────────────────────────────────────────────────────────────┘
```

### Core Capabilities
- **Multi-Format Ingestion**: Ingests `.pdf`, `.docx`, `.pptx`, and `.csv` files with structural preservation (headings, slide notes, tables, pages).
- **Dense Vector RAG**: Real vector embeddings (`sentence-transformers/all-MiniLM-L6-v2`) with cosine similarity retrieval, grounded answering, and source citations.
- **n8n Automation Integration**: Dedicated webhook ingestion endpoint with payload validation, base64 and direct URL downloading, and workflow run telemetry.
- **Safe Business Analytics**: Natural language to SQL engine with AST-based SQL validation (read-only enforcement, table whitelisting, query timeouts, row limits) and automatic narrative insights.
- **Unified Query Orchestrator**: Single endpoint (`/api/v1/query`) that automatically detects user intent and routes questions to Document RAG, Business Analytics, or a synthesized Hybrid response.
- **Production Web Dashboard**: Responsive Next.js 16 + React 19 + Tailwind CSS frontend with interactive data tables, tactile clicking animations, and live backend telemetry.

---

## 2. Technology Stack

| Layer | Technologies & Libraries | Purpose |
|---|---|---|
| **Frontend UI** | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS v4, Lucide Icons | Production web dashboard with tactile clicking effects, live health monitor, and chat |
| **API Backend** | FastAPI, Uvicorn, Pydantic v2, Pydantic-Settings | Asynchronous REST gateway, validation, CORS, error handling |
| **Document Processing** | PyMuPDF (fitz), python-docx, python-pptx, pandas | Text extraction, markdown table conversion, layout and page mapping |
| **Vector RAG & AI** | `sentence-transformers` (`all-MiniLM-L6-v2`), PyTorch, Google Gemini API | Dense vector embeddings, cosine similarity search, grounded answer synthesis |
| **Database & ORM** | PostgreSQL / SQLite, SQLAlchemy ORM, Alembic Migrations | Relational tables for documents, chunks, business metrics, and workflow tracking |
| **Security & Validation**| `sqlparse`, AST SQL Analyzer | AST read-only enforcement, table whitelist verification, timeout and row caps |
| **Workflow Automation**| n8n Webhook Integration | Automated document ingestion from cloud storage/email via webhooks |

---

## 3. Repository Structure

```
.
├── alembic/                          # Alembic database migrations
│   ├── env.py
│   └── versions/                     # Versioned migration scripts (0001 - 0003)
├── frontend/                         # Next.js 16 + Tailwind CSS frontend dashboard
│   ├── src/
│   │   ├── app/                      # Next.js App Router (layout, page, styles)
│   │   ├── components/               # Header, ChatTab, DocumentsTab, AnalyticsTab, AutomationTab
│   │   ├── lib/api.ts                # Backend API client functions
│   │   └── types/index.ts            # TypeScript data model interfaces
│   └── package.json
├── n8n/                              # n8n Automation Workflows
│   ├── document_ingestion_workflow.json # Importable n8n workflow template
│   └── README.md                     # Workflow setup and execution instructions
├── scripts/
│   └── seed_business_data.py         # Reproducible seeding for customers, products, orders
├── src/
│   └── app/
│       ├── api/                      # REST endpoints (health, documents, rag, analytics, query)
│       ├── core/                     # Config, database engine, logging, exceptions
│       ├── models/                   # SQLAlchemy ORM models (documents, chunks, analytics)
│       ├── schemas/                  # Pydantic request and response schemas
│       └── services/
│           ├── analytics/            # Text-to-SQL generator, AST validator, executor
│           ├── ingestion/            # Parsers (PDF, DOCX, PPTX, CSV), normalizer, chunker
│           ├── orchestration/        # Smart query router & hybrid synthesizer
│           └── rag/                  # Embedding generator, vector retriever, QA service
├── tests/                            # Automated test suite
├── requirements.txt                  # Python dependencies
└── README.md                         # Project documentation
```

---

## 4. Requirements & Dependencies

- **Python**: 3.11, 3.12, 3.13, or 3.14
- **Database**: PostgreSQL (recommended for production with `pgvector`) or SQLite (included for zero-config local development)
- **External Tools**: n8n (optional, for automation workflows)

### Key Python Packages
- `fastapi`, `uvicorn`: Asynchronous REST API framework and ASGI server
- `sqlalchemy`, `alembic`: Database ORM and schema migrations
- `pydantic`, `pydantic-settings`: Runtime configuration and validation
- `pymupdf`, `python-docx`, `python-pptx`, `pandas`: Document parsing engines
- `sentence-transformers`, `torch`: Dense vector embedding generation
- `sqlparse`: AST parsing and security verification for generated SQL

---

## 5. Environment Variables & Configuration

Create a `.env` file from the provided `.env.example`:

```bash
cp .env.example .env
```

| Variable | Default Value | Description |
|---|---|---|
| `APP_NAME` | `InsightFlow AI Platform` | Platform display name |
| `ENVIRONMENT` | `development` | Deployment environment (`development`, `staging`, `production`) |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `DATABASE_URL` | `sqlite:///./dev_platform.db` | SQLAlchemy connection URI (PostgreSQL or SQLite) |
| `MAX_UPLOAD_SIZE_BYTES` | `52428800` | Max file upload limit in bytes (default: 50MB) |
| `EMBEDDING_PROVIDER` | `sentence-transformers` | Embedding engine provider |
| `EMBEDDING_MODEL_NAME` | `all-MiniLM-L6-v2` | Embedding model identifier |
| `GEMINI_API_KEY` | *(optional)* | Google Gemini API key for cloud LLM inference |
| `LLM_MODEL_NAME` | `gemini-1.5-flash` | LLM model identifier |
| `LLM_TIMEOUT_SECONDS` | `30` | Network timeout for LLM inference |

---

## 6. Setup & Installation

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Run Database Migrations
Apply versioned Alembic migrations to set up document, chunk, workflow, and business analytics tables:
```bash
python -m alembic upgrade head
```

### Step 3: Seed Business Dataset
Populate the database with a realistic business dataset (customers, products, orders, order items):
```bash
python scripts/seed_business_data.py
```

### Step 4: Start the Backend Server
Launch the FastAPI ASGI application with live reloading:
```bash
uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive API documentation is accessible at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Step 5: Start the Next.js Frontend Dashboard
In a separate terminal, launch the Next.js production frontend:
```bash
cd frontend
npm run dev
```
Access the interactive dashboard in your browser at:
- **Web App**: [http://localhost:3000](http://localhost:3000)

---

## 7. n8n Workflow Integration

An exportable workflow template is provided at [`n8n/document_ingestion_workflow.json`](file:///c:/Users/91866/.gemini/antigravity/scratch/AI%20engineer%20project/n8n/document_ingestion_workflow.json).

### Setup in n8n:
1. Open your n8n workspace (desktop or cloud).
2. Go to **Workflows** -> **Import from File** and select `n8n/document_ingestion_workflow.json`.
3. In n8n workflow settings or nodes, configure the backend ingestion URL:
   - **Endpoint**: `http://localhost:8000/api/v1/documents/webhook-ingest` (or your production hostname)
   - **Method**: `POST`
   - **Content-Type**: `application/json`
4. The workflow accepts a webhook triggering document ingestion via direct Base64 payloads or remote file URLs, waits for indexing, and returns execution metrics.

---

## 8. API Reference & Example Requests

### 1. Health Check
```http
GET /health
```
**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "dependencies": {
    "database": {"status": "ok", "latency_ms": 1.2}
  }
}
```

---

### 2. Document Ingestion (Direct File Upload)
```http
POST /api/v1/documents/upload
Content-Type: multipart/form-data
```
**Curl Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@sample_report.pdf"
```

---

### 3. Webhook Document Ingestion (n8n / Automation)
```http
POST /api/v1/documents/webhook-ingest
Content-Type: application/json
```
**Request Body:**
```json
{
  "filename": "quarterly_earnings.pdf",
  "file_url": "https://example.com/docs/quarterly_earnings.pdf",
  "workflow_id": "wf-ingest-001",
  "execution_id": "exec-9921",
  "tags": ["finance", "quarterly"]
}
```

---

### 4. Vector RAG Query (Grounded Q&A with Citations)
```http
POST /api/v1/rag/query
Content-Type: application/json
```
**Request Body:**
```json
{
  "question": "What were the key revenue drivers highlighted in the report?",
  "top_k": 3
}
```
**Response (200 OK):**
```json
{
  "answer": "The primary drivers of revenue growth were cloud subscription renewals and expansion into European markets.",
  "citations": [
    {
      "document_id": "d135d564-9cb6-49ea-96b0-6435c42bc6eb",
      "filename": "quarterly_earnings.pdf",
      "page_number": 4,
      "section_title": "Executive Summary",
      "score": 0.8841
    }
  ],
  "source_chunks": [...]
}
```

---

### 5. Safe Business Analytics (Text-to-SQL)
```http
POST /api/v1/analytics/query
Content-Type: application/json
```
**Request Body:**
```json
{
  "question": "What are our top 3 best-selling products by total revenue?"
}
```
**Response (200 OK):**
```json
{
  "question": "What are our top 3 best-selling products by total revenue?",
  "generated_sql": "SELECT p.name, SUM(oi.total_price) AS total_revenue FROM order_items oi JOIN products p ON oi.product_id = p.id GROUP BY p.name ORDER BY total_revenue DESC LIMIT 3",
  "is_safe": true,
  "row_count": 3,
  "columns": ["name", "total_revenue"],
  "data": [
    {"name": "Enterprise AI Suite", "total_revenue": 48000.0},
    {"name": "Cloud Data Connector", "total_revenue": 14200.0},
    {"name": "Analytics Pro License", "total_revenue": 9500.0}
  ],
  "explanation": "Identified the top 3 best-selling products ranked by aggregated revenue.",
  "execution_time_ms": 12.4
}
```

---

### 6. Unified Query Orchestrator (Auto-Routing)
```http
POST /api/v1/query
Content-Type: application/json
```
**Request Body:**
```json
{
  "question": "Show total sales by customer and explain any payment terms in our contracts.",
  "route_override": null
}
```
**Response (200 OK):**
```json
{
  "question": "Show total sales by customer and explain any payment terms in our contracts.",
  "route_taken": "combined",
  "rag_result": { ... },
  "analytics_result": { ... },
  "final_answer": "### Business Analytics Data\nTotal sales per customer show Acquired Corp leading with $48,000...\n\n### Document Knowledge\nContract Section 4 states standard payment terms are Net-30 from invoice receipt..."
}
```

---

## 9. Security & Safeguards

- **Strict Read-Only SQL**: All Text-to-SQL queries are analyzed via an AST validator. Any mutating expressions (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `EXEC`) or multiple statements (semicolon chaining) trigger immediate validation failure.
- **Schema Whitelist**: Query execution is restricted strictly to approved tables (`customers`, `products`, `orders`, `order_items`). Access to system catalogs, SQLite masters, or Postgres `pg_catalog` is prevented.
- **Execution Safeguards**: Enforces strict row limits (default max 100 rows) and query timeout caps.
- **Corrupt File Defense**: Ingestion pre-flight inspects mime-types, file headers, and zip central directories before loading parsing engines into memory.
- **Grounded Evidence Guard**: If similarity retrieval does not meet threshold confidence or contains no evidence, the RAG service returns an explicit insufficient-evidence response without hallucination.

---

## 10. Known Limitations

1. **Cold-Start Embedding Latency**: The default local embedding model (`sentence-transformers/all-MiniLM-L6-v2`) requires PyTorch initialization on CPU, which can take 15–30 seconds during the first request on Windows environments. In production, GPU acceleration or a hosted vector embedding API is recommended.
2. **Offline Mode**: When operating in air-gapped environments, set `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` to prevent HuggingFace Hub remote connection attempts.
3. **Analytics Scope**: The SQL generator operates on normalized relational schemas up to standard complexity (multi-table JOINs, GROUP BY, aggregations). Highly nested subqueries or dynamic PL/pgSQL procedures are deliberately disallowed by the security validator.

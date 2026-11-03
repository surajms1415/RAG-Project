# n8n Document Ingestion Workflow Integration

This directory contains the importable **n8n workflow** for automated document ingestion into the **InsightFlow AI** backend.

---

## 1. Workflow Architecture

```
                  ┌─────────────────────────────────────┐
                  │    n8n Webhook Trigger Node         │
                  │ POST /webhook/document-ingestion    │
                  └──────────────────┬──────────────────┘
                                     │
                                     ▼
                  ┌─────────────────────────────────────┐
                  │       Input Validation Node         │
                  │ (Filename, .pdf/.docx/.pptx/.csv,   │
                  │      file_base64 / file_url)        │
                  └──────────┬────────────────┬─────────┘
                             │ Valid          │ Invalid
                             ▼                ▼
         ┌───────────────────────────┐  ┌─────────────────────────┐
         │ HTTP Request to Backend   │  │ Respond to Webhook:     │
         │ POST /documents/          │  │ HTTP 400 Bad Request    │
         │      webhook-ingest       │  └─────────────────────────┘
         └─────────────┬─────────────┘
                       │
          ┌────────────┴────────────┐
          │ HTTP 201                │ Non-201 / Error
          ▼                         ▼
┌───────────────────────────┐  ┌─────────────────────────────┐
│ Respond to Webhook:       │  │ Respond to Webhook:         │
│ HTTP 200 OK               │  │ HTTP 500 / 502 Failure      │
│ (Doc ID, Job ID, Status)  │  │ (Backend Error Details)     │
└───────────────────────────┘  └─────────────────────────────┘
```

The workflow acts as an external orchestration entrypoint:
1. Receives an automated ingestion request (scheduled jobs, email attachments, folder watchers, or external webhooks).
2. Performs pre-flight input validation in n8n.
3. Forwards the payload to the existing FastAPI backend (`POST /api/v1/documents/webhook-ingest`).
4. The Python backend performs text extraction, table parsing, chunking, real embeddings, and vector storage.
5. Returns a structured JSON notification to the caller with ingestion status, document ID, and job details.

---

## 2. Environment Variables

Configure these environment variables in your n8n runtime (`.env` or Docker container environment):

| Variable | Default Value | Description |
|---|---|---|
| `BACKEND_API_URL` | `http://localhost:8000` | The base URL of the FastAPI backend application. In Docker network, typically `http://backend:8000` or `http://host.docker.internal:8000`. |
| `N8N_WEBHOOK_URL` | `http://localhost:5678/webhook/document-ingestion` | Webhook URL where clients/systems send document ingestion payloads. |

---

## 3. Webhook URLs

- **Production Webhook URL**:
  `POST http://<n8n-host>:5678/webhook/document-ingestion`
- **Test Webhook URL (n8n Editor Mode)**:
  `POST http://<n8n-host>:5678/webhook-test/document-ingestion`

---

## 4. Request Payload Formats

The webhook accepts a JSON payload with either `file_base64` or `file_url`:

### Option A: Ingestion via Base64 File Content
```json
{
  "filename": "q3_financial_report.pdf",
  "file_base64": "JVBERi0xLjQKJcOkw7zDtsOfCjIgMCBvYmoK...",
  "metadata": {
    "source": "n8n_automated_watchdog",
    "department": "Finance"
  }
}
```

### Option B: Ingestion via Downloadable URL
```json
{
  "filename": "product_architecture.docx",
  "file_url": "https://example.com/docs/product_architecture.docx",
  "metadata": {
    "source": "cloud_storage",
    "version": "1.4"
  }
}
```

---

## 5. Webhook Responses

### Success Response (`200 OK`)
```json
{
  "status": "success",
  "message": "Document successfully ingested via automation webhook.",
  "document_id": "b9643d9b-314d-45db-bdf2-f8c7e96b7ad2",
  "job_id": "62eb74f1-3329-4509-9b98-0cfa0eb0589a",
  "is_duplicate": false,
  "title": "q3_financial_report.pdf",
  "file_type": "pdf",
  "workflow_execution_id": "104"
}
```

### Validation Error Response (`400 Bad Request`)
```json
{
  "status": "error",
  "error": "Validation Error: Unsupported file extension \".exe\". Allowed: .pdf, .docx, .pptx, .csv",
  "received_payload": {
    "filename": "payload.exe"
  }
}
```

### Backend Ingestion Failure Response (`500 / 422`)
```json
{
  "status": "failure",
  "error": "Document ingestion backend processing failed.",
  "statusCode": 422,
  "backend_details": {
    "error": {
      "type": "CorruptFileError",
      "message": "Invalid PDF header. File is corrupt or not a valid PDF."
    }
  },
  "workflow_execution_id": "105"
}
```

---

## 6. How to Import Workflow into n8n

1. Open your n8n web interface (e.g. `http://localhost:5678`).
2. Go to **Workflows** > **Import from File...**
3. Select `n8n/document_ingestion_workflow.json`.
4. Ensure the `BACKEND_API_URL` environment variable is accessible to n8n (or update the HTTP Request node URL if using a specific hostname).
5. Toggle the workflow to **Active** (in top right corner).

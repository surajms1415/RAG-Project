import base64
import pytest
from unittest.mock import patch
from fastapi import status

from src.app.models.analytics import Customer, Order, Product
from src.app.models.document import Chunk, Document
from src.app.services.rag.llm import MockLLMProvider
from src.app.services.orchestration.router import QueryRoute


def test_workflow_1_document_upload_index_and_qa_citations(client, sample_pdf_bytes):
    """Workflow 1: Upload a document -> process & index it -> ask a question -> receive grounded answer with citations."""
    # Step 1: Upload document through API
    upload_res = client.post(
        "/api/v1/documents/upload",
        files={"file": ("financial_annual_2026.pdf", sample_pdf_bytes, "application/pdf")},
    )
    assert upload_res.status_code == status.HTTP_201_CREATED
    data = upload_res.json()
    doc_id = data["document"]["id"]
    assert data["document"]["status"] == "COMPLETED"

    # Verify chunks and embeddings were created
    chunks_res = client.get(f"/api/v1/documents/{doc_id}/chunks")
    assert chunks_res.status_code == status.HTTP_200_OK
    chunks = chunks_res.json()
    assert len(chunks) > 0

    # Step 2: Query the RAG endpoint
    with patch("src.app.services.rag.qa_service.get_llm_provider", return_value=MockLLMProvider()):
        query_res = client.post(
            "/api/v1/rag/query",
            json={"question": "What was the revenue and EBITDA growth?"},
        )
        assert query_res.status_code == status.HTTP_200_OK
        q_data = query_res.json()

        # Step 3: Validate grounded answer and citations
        assert q_data["has_sufficient_evidence"] is True
        assert len(q_data["citations"]) > 0
        citation = q_data["citations"][0]
        assert citation["document_id"] == doc_id
        assert citation["filename"] == "financial_annual_2026.pdf"
        assert citation["page_number"] is not None
        assert "revenue" in q_data["answer"].lower() or "growth" in q_data["answer"].lower() or "financial" in q_data["answer"].lower()


def test_workflow_2_n8n_webhook_ingestion(client, sample_csv_bytes):
    """Workflow 2: Trigger document ingestion through webhook -> backend processes -> receives outcome."""
    csv_b64 = base64.b64encode(sample_csv_bytes).decode("utf-8")
    workflow_exec_id = "n8n-exec-test-999"

    # Trigger automation webhook endpoint
    webhook_res = client.post(
        "/api/v1/documents/webhook-ingest",
        json={
            "filename": "infra_cost_report.csv",
            "file_base64": csv_b64,
            "metadata": {"source": "n8n_weekly_sync", "department": "DevOps"},
            "workflow_id": workflow_exec_id,
        },
    )
    assert webhook_res.status_code == status.HTTP_201_CREATED
    outcome = webhook_res.json()

    assert outcome["document"]["title"] == "infra_cost_report.csv"
    assert outcome["document"]["status"] == "COMPLETED"
    assert outcome["job_id"] is not None
    assert outcome["is_duplicate"] is False
    assert "automation webhook" in outcome["message"].lower()

    # Verify duplicate handling via webhook
    dup_res = client.post(
        "/api/v1/documents/webhook-ingest",
        json={
            "filename": "infra_cost_report_copy.csv",
            "file_base64": csv_b64,
            "workflow_id": "n8n-exec-test-1000",
        },
    )
    assert dup_res.status_code == status.HTTP_201_CREATED
    dup_data = dup_res.json()
    assert dup_data["is_duplicate"] is True
    assert dup_data["document"]["id"] == outcome["document"]["id"]


def test_workflow_3_business_analytics_sql_and_explanation(client, db_session):
    """Workflow 3: Business dataset -> Natural language analytics question -> Safe SQL -> Results & explanation."""
    # Seed test analytics records if not present
    c1 = Customer(
        id="cust-001",
        name="Acme Global Industries",
        email="procurement@acme.com",
        segment="Enterprise",
        country="United States",
        city="New York",
    )
    p1 = Product(
        id="prod-001",
        name="AI Workflow Platform",
        category="Software",
        unit_price=1200.0,
        cost=150.0,
        stock_quantity=999,
    )
    db_session.add_all([c1, p1])
    db_session.flush()

    o1 = Order(
        id="ord-1001",
        customer_id="cust-001",
        status="Completed",
        total_amount=10200.0,
        shipping_city="New York",
    )
    db_session.add(o1)
    db_session.flush()

    # Test schema inspection endpoint
    schema_res = client.get("/api/v1/analytics/schema")
    assert schema_res.status_code == status.HTTP_200_OK
    schema_data = schema_res.json()
    assert "customers" in schema_data["approved_tables"]
    assert "products" in schema_data["approved_tables"]

    # Natural-language business question
    query_res = client.post(
        "/api/v1/analytics/query",
        json={"question": "What are our top products by revenue?", "max_rows": 5},
    )
    assert query_res.status_code == status.HTTP_200_OK
    data = query_res.json()

    assert "SELECT" in data["sql_query"].upper()
    assert "FROM" in data["sql_query"].upper()
    assert data["row_count"] >= 0
    assert len(data["explanation"]) > 0
    assert "execution_time_ms" in data["summary"]


def test_workflow_4_unified_query_routing(client, sample_docx_bytes):
    """Workflow 4: Verify combined document and business-data questions routing."""
    # Seed a document first
    client.post(
        "/api/v1/documents/upload",
        files={"file": ("architecture_overview.docx", sample_docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )

    with patch("src.app.services.rag.qa_service.get_llm_provider", return_value=MockLLMProvider()):
        # 1. Structured analytics routing
        res_analytics = client.post(
            "/api/v1/query",
            json={"question": "What is our customer order sales volume?"},
        )
        assert res_analytics.status_code == status.HTTP_200_OK
        data_a = res_analytics.json()
        assert data_a["route_used"] == QueryRoute.STRUCTURED_ANALYTICS.value
        assert data_a["sql_query"] is not None

        # 2. Document RAG routing
        res_rag = client.post(
            "/api/v1/query",
            json={"question": "What is described in the architecture specification document?"},
        )
        assert res_rag.status_code == status.HTTP_200_OK
        data_r = res_rag.json()
        assert data_r["route_used"] == QueryRoute.DOCUMENT_RAG.value
        assert len(data_r["citations"]) > 0

        # 3. Combined routing
        res_comb = client.post(
            "/api/v1/query",
            json={
                "question": "What does the architecture document say about our product and order systems?",
                "route": "combined",
            },
        )
        assert res_comb.status_code == status.HTTP_200_OK
        data_c = res_comb.json()
        assert data_c["route_used"] == QueryRoute.COMBINED.value
        assert "Document Evidence:" in data_c["answer"]
        assert "Structured Business Analytics:" in data_c["answer"]

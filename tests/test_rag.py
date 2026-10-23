import pytest
from unittest.mock import patch, MagicMock
from fastapi import status

from src.app.core.exceptions import (
    EmbeddingError,
    LLMConfigurationError,
    LLMTimeoutError,
)
from src.app.models.document import Chunk, Document
from src.app.models.enums import DocumentStatus
from src.app.services.ingestion.pipeline import IngestionPipeline
from src.app.services.rag.embeddings import (
    SentenceTransformersProvider,
    GeminiEmbeddingProvider,
    get_embedding_service,
)
from src.app.services.rag.llm import GeminiLLMProvider, MockLLMProvider
from src.app.services.rag.qa_service import QAService, INSUFFICIENT_EVIDENCE_PHRASE
from src.app.services.rag.retrieval import retrieve_relevant_chunks


def test_real_embeddings_generation():
    """Task 3: Generate real embeddings using configured provider (SentenceTransformers)."""
    provider = SentenceTransformersProvider()
    vector = provider.embed_text("Cloud architecture scalability and ingestion.")
    
    # SentenceTransformer all-MiniLM-L6-v2 outputs real 384-dimensional float vector
    assert isinstance(vector, list)
    assert len(vector) == 384
    assert all(isinstance(x, float) for x in vector)

    # Empty text error handling
    with pytest.raises(EmbeddingError):
        provider.embed_text("   ")


def test_ingestion_stores_embeddings_and_metadata(db_session, sample_pdf_bytes):
    """Tasks 1, 2, 4: Ingestion preserves document IDs, filenames, page numbers, and stores real embeddings."""
    pipeline = IngestionPipeline(db_session)
    doc, job, _ = pipeline.process_file("annual_financial_report.pdf", sample_pdf_bytes)

    assert doc.status == DocumentStatus.COMPLETED
    chunks = db_session.query(Chunk).filter(Chunk.document_id == doc.id).all()
    assert len(chunks) > 0

    for c in chunks:
        # Document ID and version preservation
        assert c.document_id == doc.id
        assert c.document_version_id is not None
        # Metadata preservation
        assert c.chunk_metadata.get("filename") == "annual_financial_report.pdf"
        assert c.page_number is not None
        # Real embedding stored in database
        assert c.embedding is not None
        assert len(c.embedding) == 384


def test_similarity_search_retrieval(db_session, sample_pdf_bytes, sample_pptx_bytes):
    """Task 5: Implement similarity search to retrieve the most relevant chunks."""
    pipeline = IngestionPipeline(db_session)
    doc_pdf, _, _ = pipeline.process_file("financial.pdf", sample_pdf_bytes)
    doc_pptx, _, _ = pipeline.process_file("roadmap.pptx", sample_pptx_bytes)

    # Query about financial figures
    fin_results = retrieve_relevant_chunks(db_session, query="What was the revenue and EBITDA growth?", top_k=2)
    assert len(fin_results) > 0
    # Top result should be from the financial document
    assert fin_results[0].document_id == doc_pdf.id
    assert "Revenue" in fin_results[0].content or "EBITDA" in fin_results[0].content
    assert fin_results[0].similarity_score > 0.30

    # Query about roadmap
    roadmap_results = retrieve_relevant_chunks(db_session, query="What are the phase milestones for AI?", top_k=2)
    assert len(roadmap_results) > 0
    assert roadmap_results[0].document_id == doc_pptx.id
    assert "Milestones" in roadmap_results[0].content or "Roadmap" in roadmap_results[0].content


def test_rag_grounded_answer_and_citations(db_session, sample_pdf_bytes):
    """Task 6: Grounded answer with source citations."""
    pipeline = IngestionPipeline(db_session)
    doc, _, _ = pipeline.process_file("financial_q2.pdf", sample_pdf_bytes)

    qa = QAService(db_session)
    # Use deterministic mock provider for testing grounded answer logic
    qa.llm_provider = MockLLMProvider()

    result = qa.answer_question("What was the annual revenue growth?")
    assert result.has_sufficient_evidence is True
    assert "Revenue grew by 24%" in result.answer
    assert len(result.citations) > 0

    citation = result.citations[0]
    assert citation.document_id == doc.id
    assert citation.filename == "financial_q2.pdf"
    assert citation.page_number is not None
    assert citation.similarity_score > 0.0
    assert len(citation.snippet) > 0


def test_unanswerable_question_insufficient_evidence(db_session, sample_pdf_bytes):
    """Task 7: Returns honest insufficient-evidence response when evidence is missing."""
    pipeline = IngestionPipeline(db_session)
    pipeline.process_file("financial.pdf", sample_pdf_bytes)

    qa = QAService(db_session)
    qa.llm_provider = MockLLMProvider()

    # Query completely unrelated to financial report
    result = qa.answer_question("What is the recipe for chocolate lava cake?")
    assert result.has_sufficient_evidence is False
    assert result.answer == INSUFFICIENT_EVIDENCE_PHRASE
    assert result.citations == []


def test_missing_api_key_error_handling(db_session):
    """Task 9: Error handling for missing API keys with Gemini provider."""
    provider = GeminiLLMProvider(api_key=None)
    with pytest.raises(LLMConfigurationError) as exc_info:
        provider.generate_grounded_answer("test question", ["some context"])
    assert "GEMINI_API_KEY is not configured" in str(exc_info.value)

    # Gemini embedding provider without key
    with pytest.raises(LLMConfigurationError):
        GeminiEmbeddingProvider(api_key="")


def test_llm_timeout_error_handling():
    """Task 9: Error handling for LLM timeouts."""
    provider = GeminiLLMProvider(api_key="valid_looking_key_12345")

    with patch("concurrent.futures.Future.result", side_effect=Exception("timeout")) as mock_call:
        from concurrent.futures import TimeoutError as FuturesTimeoutError
        mock_call.side_effect = FuturesTimeoutError()

        with pytest.raises(LLMTimeoutError) as exc_info:
            provider.generate_grounded_answer("test question", ["context snippet"])
        assert "timed out" in str(exc_info.value).lower()


def test_rag_api_endpoint(client, sample_docx_bytes):
    """Task 8: FastAPI endpoint /api/v1/rag/query returns answer, citations, and metadata."""
    # First, upload document via API
    upload_res = client.post(
        "/api/v1/documents/upload",
        files={"file": ("architecture_spec.docx", sample_docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )
    assert upload_res.status_code == status.HTTP_201_CREATED

    with patch("src.app.services.rag.qa_service.get_llm_provider", return_value=MockLLMProvider()):
        # Query known content
        query_res = client.post(
            "/api/v1/rag/query",
            json={"question": "What is the SLA for the Parser Engine?", "top_k": 3},
        )
        assert query_res.status_code == status.HTTP_200_OK
        data = query_res.json()
        assert data["has_sufficient_evidence"] is True
        assert len(data["citations"]) > 0
        assert data["citations"][0]["filename"] == "architecture_spec.docx"

        # Query unanswerable content
        unanswerable_res = client.post(
            "/api/v1/rag/query",
            json={"question": "What is the capital of Mars?"},
        )
        assert unanswerable_res.status_code == status.HTTP_200_OK
        unanswerable_data = unanswerable_res.json()
        assert unanswerable_data["has_sufficient_evidence"] is False
        assert unanswerable_data["answer"] == INSUFFICIENT_EVIDENCE_PHRASE
        assert unanswerable_data["citations"] == []

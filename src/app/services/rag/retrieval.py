import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import numpy as np
from sqlalchemy.orm import Session

from src.app.core.config import get_settings
from src.app.models.document import Chunk, Document
from src.app.services.rag.embeddings import get_embedding_service

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class SimilaritySearchResult:
    """Represents a retrieved chunk matching the query with score and metadata."""

    chunk_id: str
    document_id: str
    filename: str
    content: str
    page_number: Optional[int]
    section_title: Optional[str]
    similarity_score: float
    metadata: Dict[str, Any]


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes cosine similarity between two numerical vectors."""
    a = np.array(v1, dtype=np.float32)
    b = np.array(v2, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


def retrieve_relevant_chunks(
    db: Session,
    query: str,
    top_k: Optional[int] = None,
    similarity_threshold: Optional[float] = None,
    document_id: Optional[str] = None,
) -> List[SimilaritySearchResult]:
    """Performs semantic similarity search against stored chunk embeddings."""
    k = top_k or settings.RAG_TOP_K
    threshold = similarity_threshold if similarity_threshold is not None else settings.RAG_SIMILARITY_THRESHOLD

    if not query or not query.strip():
        return []

    # 1. Embed query vector using real embedding provider
    embedding_service = get_embedding_service()
    query_vector = embedding_service.embed_text(query.strip())

    # 2. Query stored chunks from database
    chunk_query = db.query(Chunk, Document.title).join(Document, Chunk.document_id == Document.id)
    if document_id:
        chunk_query = chunk_query.filter(Chunk.document_id == document_id)

    db_results = chunk_query.all()
    if not db_results:
        return []

    scored_chunks: List[SimilaritySearchResult] = []

    # 3. Calculate similarities
    for chunk, doc_title in db_results:
        emb = chunk.embedding
        if not emb:
            # On-demand embedding generation if missing
            try:
                emb = embedding_service.embed_text(chunk.content)
                chunk.embedding = emb
                db.commit()
            except Exception as e:
                logger.warning(f"Could not compute embedding for chunk {chunk.id}: {e}")
                continue

        score = cosine_similarity(query_vector, emb)

        filename = (chunk.chunk_metadata or {}).get("filename") or doc_title or "unknown_doc"

        if score >= threshold:
            scored_chunks.append(
                SimilaritySearchResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    filename=filename,
                    content=chunk.content,
                    page_number=chunk.page_number,
                    section_title=chunk.section_title,
                    similarity_score=round(score, 4),
                    metadata=chunk.chunk_metadata or {},
                )
            )

    # 4. Sort descending by similarity score
    scored_chunks.sort(key=lambda x: x.similarity_score, reverse=True)

    return scored_chunks[:k]

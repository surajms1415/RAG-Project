import logging
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.app.core.config import get_settings
from src.app.models.conversation import Message
from src.app.models.enums import MessageRole
from src.app.services.rag.llm import get_llm_provider
from src.app.services.rag.retrieval import SimilaritySearchResult, retrieve_relevant_chunks

logger = logging.getLogger(__name__)
settings = get_settings()

INSUFFICIENT_EVIDENCE_PHRASE = (
    "I do not have sufficient evidence in the provided documents to answer this question."
)


class CitationItem(BaseModel):
    document_id: str
    filename: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    chunk_id: str
    snippet: str
    similarity_score: float


class QAResult(BaseModel):
    question: str
    answer: str
    citations: List[CitationItem] = Field(default_factory=list)
    has_sufficient_evidence: bool
    retrieved_chunks_count: int


class QAService:
    """Orchestrates similarity search retrieval, grounding, citation tracking, and answer generation."""

    def __init__(self, db: Session):
        self.db = db
        self.llm_provider = get_llm_provider()

    def answer_question(
        self,
        question: str,
        top_k: Optional[int] = None,
        document_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
    ) -> QAResult:
        logger.info(f"Processing question: '{question}' (doc_filter: {document_id})")

        # 1. Similarity search retrieval
        retrieved_chunks = retrieve_relevant_chunks(
            db=self.db,
            query=question,
            top_k=top_k,
            document_id=document_id,
        )

        # 2. Honest fallback if no relevant evidence is found
        if not retrieved_chunks:
            logger.info("Zero matching chunks above similarity threshold. Returning insufficient evidence response.")
            result = QAResult(
                question=question,
                answer=INSUFFICIENT_EVIDENCE_PHRASE,
                citations=[],
                has_sufficient_evidence=False,
                retrieved_chunks_count=0,
            )
            self._save_conversation_turn(conversation_id, question, result)
            return result

        # 3. Format retrieved context blocks for LLM
        context_blocks = []
        for c in retrieved_chunks:
            page_info = f"Page {c.page_number}" if c.page_number is not None else "N/A"
            section_info = f"Section: {c.section_title}" if c.section_title else "N/A"
            block = (
                f"[{c.filename} | {page_info} | {section_info}]\n"
                f"{c.content}"
            )
            context_blocks.append(block)

        # 4. Invoke LLM for grounded answer
        llm_response = self.llm_provider.generate_grounded_answer(
            question=question,
            context_blocks=context_blocks,
        )

        # 5. Check if LLM determined context was insufficient
        is_insufficient = (
            "insufficient evidence" in llm_response.lower()
            or "do not have sufficient evidence" in llm_response.lower()
        )

        if is_insufficient:
            citations = []
            has_sufficient = False
            final_answer = INSUFFICIENT_EVIDENCE_PHRASE
        else:
            has_sufficient = True
            final_answer = llm_response
            citations = [
                CitationItem(
                    document_id=c.document_id,
                    filename=c.filename,
                    page_number=c.page_number,
                    section_title=c.section_title,
                    chunk_id=c.chunk_id,
                    snippet=c.content[:200] + ("..." if len(c.content) > 200 else ""),
                    similarity_score=c.similarity_score,
                )
                for c in retrieved_chunks
            ]

        result = QAResult(
            question=question,
            answer=final_answer,
            citations=citations,
            has_sufficient_evidence=has_sufficient,
            retrieved_chunks_count=len(retrieved_chunks),
        )

        self._save_conversation_turn(conversation_id, question, result)
        return result

    def _save_conversation_turn(
        self,
        conversation_id: Optional[str],
        question: str,
        result: QAResult,
    ) -> None:
        """Persists turn to database if conversation_id is provided."""
        if not conversation_id:
            return
        try:
            user_msg = Message(
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content=question,
            )
            self.db.add(user_msg)

            assistant_msg = Message(
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=result.answer,
                citations=[c.model_dump() for c in result.citations],
            )
            self.db.add(assistant_msg)
            self.db.commit()
        except Exception as e:
            logger.warning(f"Failed to record message turn for conversation {conversation_id}: {e}")
            self.db.rollback()

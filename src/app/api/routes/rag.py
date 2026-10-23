from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from src.app.api.deps import get_db
from src.app.schemas.rag import QueryRequest, QueryResponse
from src.app.services.rag.qa_service import QAService

router = APIRouter(prefix="/rag", tags=["Retrieval-Augmented Generation"])


@router.post("/query", response_model=QueryResponse, status_code=status.HTTP_200_OK)
def query_knowledge_base(
    payload: QueryRequest,
    db: Session = Depends(get_db),
) -> QueryResponse:
    """Answers a user inquiry using similarity retrieval, grounded LLM generation, and source citations."""
    qa_service = QAService(db)
    result = qa_service.answer_question(
        question=payload.question,
        top_k=payload.top_k,
        document_id=payload.document_id,
        conversation_id=payload.conversation_id,
    )
    return QueryResponse.model_validate(result)

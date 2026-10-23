from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class QueryRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    question: str = Field(..., min_length=2, description="User query or inquiry to ask the knowledge base.")
    document_id: Optional[str] = Field(default=None, description="Optional document ID to restrict search scope.")
    top_k: Optional[int] = Field(default=None, ge=1, le=20, description="Max number of chunks to retrieve.")
    conversation_id: Optional[str] = Field(default=None, description="Optional conversation session ID to persist message history.")


class CitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    filename: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    chunk_id: str
    snippet: str
    similarity_score: float


class QueryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    question: str
    answer: str
    citations: List[CitationResponse] = Field(default_factory=list)
    has_sufficient_evidence: bool
    retrieved_chunks_count: int

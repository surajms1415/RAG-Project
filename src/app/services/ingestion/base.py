from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ExtractedTable:
    """Represents a structured table extracted from a document."""

    headers: List[str]
    rows: List[List[str]]
    markdown: str
    page_number: Optional[int] = None
    title: Optional[str] = None


@dataclass
class ExtractedChunk:
    """Represents an atomic extracted unit with semantic and positional metadata."""

    content: str
    chunk_index: int
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    token_count: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractionResult:
    """Consolidated output from a document parser."""

    raw_text: str
    chunks: List[ExtractedChunk]
    tables: List[ExtractedTable] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    page_count: Optional[int] = None
    file_size_bytes: int = 0


class BaseDocumentParser(ABC):
    """Abstract base class for document type parsers."""

    @abstractmethod
    def extract(self, file_bytes: bytes, filename: str) -> ExtractionResult:
        """Parses raw document bytes and returns extracted content, tables, and metadata."""
        pass

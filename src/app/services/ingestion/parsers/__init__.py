from typing import Dict, Type
from src.app.models.enums import FileType
from src.app.services.ingestion.base import BaseDocumentParser
from src.app.services.ingestion.parsers.pdf_parser import PDFParser
from src.app.services.ingestion.parsers.docx_parser import DOCXParser
from src.app.services.ingestion.parsers.pptx_parser import PPTXParser
from src.app.services.ingestion.parsers.csv_parser import CSVParser

PARSER_REGISTRY: Dict[FileType, Type[BaseDocumentParser]] = {
    FileType.PDF: PDFParser,
    FileType.DOCX: DOCXParser,
    FileType.PPTX: PPTXParser,
    FileType.CSV: CSVParser,
}


def get_parser_for_type(file_type: FileType) -> BaseDocumentParser:
    """Returns an instantiated parser for the given file type."""
    parser_cls = PARSER_REGISTRY.get(file_type)
    if not parser_cls:
        raise ValueError(f"No parser registered for file type: {file_type}")
    return parser_cls()

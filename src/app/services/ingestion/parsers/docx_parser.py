import io
import logging
from typing import List
import docx

from src.app.core.exceptions import CorruptFileError
from src.app.services.ingestion.base import (
    BaseDocumentParser,
    ExtractedChunk,
    ExtractedTable,
    ExtractionResult,
)
from src.app.services.ingestion.normalizer import (
    estimate_tokens,
    format_chunk_with_context,
    normalize_text,
)

logger = logging.getLogger(__name__)


class DOCXParser(BaseDocumentParser):
    """Extracts text, hierarchical sections, and tables from DOCX documents."""

    def extract(self, file_bytes: bytes, filename: str) -> ExtractionResult:
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
        except Exception as exc:
            raise CorruptFileError(f"Failed to parse DOCX document: {exc}", details={"filename": filename, "error": str(exc)})

        chunks: List[ExtractedChunk] = []
        extracted_tables: List[ExtractedTable] = []
        raw_text_parts: List[str] = []
        chunk_idx = 0

        # Core properties metadata
        extracted_metadata = {
            "title": doc.core_properties.title or filename,
            "author": doc.core_properties.author or "",
            "subject": doc.core_properties.subject or "",
            "created": str(doc.core_properties.created) if doc.core_properties.created else "",
            "modified": str(doc.core_properties.modified) if doc.core_properties.modified else "",
        }

        current_section = "General"
        current_section_paragraphs: List[str] = []

        def flush_section_chunk():
            nonlocal chunk_idx, current_section_paragraphs
            if current_section_paragraphs:
                section_text = normalize_text("\n\n".join(current_section_paragraphs))
                if section_text:
                    raw_text_parts.append(section_text)
                    content = format_chunk_with_context(
                        content=section_text,
                        section_title=current_section,
                        page_number=None,
                    )
                    chunks.append(
                        ExtractedChunk(
                            content=content,
                            chunk_index=chunk_idx,
                            section_title=current_section,
                            page_number=None,
                            token_count=estimate_tokens(content),
                            metadata={"section": current_section, "type": "paragraph_block"},
                        )
                    )
                    chunk_idx += 1
                current_section_paragraphs = []

        # Iterate through document paragraphs
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue

            style_name = p.style.name.lower() if p.style else ""
            if "heading" in style_name:
                flush_section_chunk()
                current_section = text
            else:
                current_section_paragraphs.append(text)

        flush_section_chunk()

        # Iterate through tables
        for t_idx, table in enumerate(doc.tables):
            if not table.rows:
                continue

            # First row as header
            headers = [normalize_text(cell.text) for cell in table.rows[0].cells]
            rows: List[List[str]] = []
            for row in table.rows[1:]:
                row_data = [normalize_text(cell.text) for cell in row.cells]
                rows.append(row_data)

            md_lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
            for r in rows:
                md_lines.append("| " + " | ".join(r) + " |")
            md_table = "\n".join(md_lines)

            table_title = f"Table {t_idx + 1} ({current_section})"
            extracted_tables.append(
                ExtractedTable(
                    headers=headers,
                    rows=rows,
                    markdown=md_table,
                    title=table_title,
                )
            )

            tbl_content = format_chunk_with_context(
                content=f"### {table_title}\n{md_table}",
                section_title=table_title,
                page_number=None,
            )
            chunks.append(
                ExtractedChunk(
                    content=tbl_content,
                    chunk_index=chunk_idx,
                    section_title=table_title,
                    page_number=None,
                    token_count=estimate_tokens(tbl_content),
                    metadata={"section": current_section, "type": "table", "headers": headers},
                )
            )
            chunk_idx += 1
            raw_text_parts.append(md_table)

        total_text = "\n\n".join(raw_text_parts)
        if not total_text.strip():
            raise CorruptFileError(
                "DOCX document contains no text or tables.",
                details={"filename": filename},
            )

        return ExtractionResult(
            raw_text=total_text,
            chunks=chunks,
            tables=extracted_tables,
            metadata=extracted_metadata,
            page_count=None,
            file_size_bytes=len(file_bytes),
        )

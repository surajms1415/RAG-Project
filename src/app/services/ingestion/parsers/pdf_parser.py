import logging
from typing import List
import pymupdf

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


class PDFParser(BaseDocumentParser):
    """Extracts text, structured tables, and page metadata from PDF documents using PyMuPDF."""

    def extract(self, file_bytes: bytes, filename: str) -> ExtractionResult:
        try:
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        except Exception as exc:
            raise CorruptFileError(f"Failed to open or decrypt PDF: {exc}", details={"filename": filename, "error": str(exc)})

        if doc.is_encrypted:
            raise CorruptFileError("Encrypted/password-protected PDFs are not supported.", details={"filename": filename})

        page_count = len(doc)
        if page_count == 0:
            raise CorruptFileError("PDF contains 0 pages.", details={"filename": filename})

        raw_text_parts: List[str] = []
        chunks: List[ExtractedChunk] = []
        extracted_tables: List[ExtractedTable] = []
        chunk_idx = 0

        # Extract doc metadata
        meta = doc.metadata or {}
        raw_title = meta.get("title")
        if not raw_title or raw_title.strip() in ("", "(anonymous)"):
            title = filename
        else:
            title = raw_title.strip()

        extracted_metadata = {
            "title": title,
            "author": meta.get("author") or "",
            "subject": meta.get("subject") or "",
            "producer": meta.get("producer") or "",
            "creation_date": meta.get("creationDate") or "",
            "page_count": page_count,
        }

        current_section = "Introduction"

        for page_idx in range(page_count):
            page_num = page_idx + 1
            page = doc[page_idx]

            # Extract tables if available
            try:
                tabs = page.find_tables()
                for t_idx, tab in enumerate(tabs):
                    table_data = tab.extract()
                    if table_data and len(table_data) > 0:
                        headers = [str(col).strip() if col is not None else "" for col in table_data[0]]
                        rows = [
                            [str(cell).strip() if cell is not None else "" for cell in r]
                            for r in table_data[1:]
                        ]
                        # Create markdown table
                        md_lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
                        for r in rows:
                            md_lines.append("| " + " | ".join(r) + " |")
                        md_table = "\n".join(md_lines)

                        extracted_tables.append(
                            ExtractedTable(
                                headers=headers,
                                rows=rows,
                                markdown=md_table,
                                page_number=page_num,
                                title=f"Table {t_idx + 1} (Page {page_num})",
                            )
                        )
            except Exception as e:
                logger.debug(f"Table extraction skipped on page {page_num}: {e}")

            # Extract text blocks
            text = page.get_text("text")
            cleaned_text = normalize_text(text)

            if cleaned_text:
                raw_text_parts.append(cleaned_text)

                # Detect potential section headers from the first short line
                first_line = cleaned_text.split("\n")[0].strip()
                if 3 < len(first_line) < 80 and not first_line.endswith("."):
                    current_section = first_line

                content_with_ctx = format_chunk_with_context(
                    content=cleaned_text,
                    section_title=current_section,
                    page_number=page_num,
                )

                chunk = ExtractedChunk(
                    content=content_with_ctx,
                    chunk_index=chunk_idx,
                    section_title=current_section,
                    page_number=page_num,
                    token_count=estimate_tokens(content_with_ctx),
                    metadata={"page": page_num, "type": "page_text"},
                )
                chunks.append(chunk)
                chunk_idx += 1

        # Also append any extracted tables as specialized chunks for retrieval
        for tbl in extracted_tables:
            tbl_content = format_chunk_with_context(
                content=f"### {tbl.title}\n{tbl.markdown}",
                section_title=tbl.title,
                page_number=tbl.page_number,
            )
            chunks.append(
                ExtractedChunk(
                    content=tbl_content,
                    chunk_index=chunk_idx,
                    section_title=tbl.title,
                    page_number=tbl.page_number,
                    token_count=estimate_tokens(tbl_content),
                    metadata={"page": tbl.page_number, "type": "table", "headers": tbl.headers},
                )
            )
            chunk_idx += 1

        total_text = "\n\n".join(raw_text_parts)
        if not total_text.strip() and len(extracted_tables) == 0:
            raise CorruptFileError(
                "PDF contains no extractable text or tables (might be scanned or empty images).",
                details={"filename": filename, "page_count": page_count},
            )

        doc.close()

        return ExtractionResult(
            raw_text=total_text,
            chunks=chunks,
            tables=extracted_tables,
            metadata=extracted_metadata,
            page_count=page_count,
            file_size_bytes=len(file_bytes),
        )

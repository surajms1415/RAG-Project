import io
import logging
from typing import List
import pptx

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


class PPTXParser(BaseDocumentParser):
    """Extracts text, slide titles, tables, and notes from PPTX presentations."""

    def extract(self, file_bytes: bytes, filename: str) -> ExtractionResult:
        try:
            prs = pptx.Presentation(io.BytesIO(file_bytes))
        except Exception as exc:
            raise CorruptFileError(f"Failed to parse PPTX presentation: {exc}", details={"filename": filename, "error": str(exc)})

        slide_count = len(prs.slides)
        if slide_count == 0:
            raise CorruptFileError("PPTX presentation contains 0 slides.", details={"filename": filename})

        chunks: List[ExtractedChunk] = []
        extracted_tables: List[ExtractedTable] = []
        raw_text_parts: List[str] = []
        chunk_idx = 0

        extracted_metadata = {
            "title": filename,
            "slide_count": slide_count,
        }

        try:
            core_props = prs.core_properties
            if core_props:
                if core_props.title:
                    extracted_metadata["title"] = core_props.title
                if core_props.author:
                    extracted_metadata["author"] = core_props.author
                if core_props.created:
                    extracted_metadata["created"] = str(core_props.created)
        except Exception as e:
            logger.debug(f"Could not read core_properties from PPTX: {e}")

        for slide_idx, slide in enumerate(prs.slides):
            slide_num = slide_idx + 1
            slide_title = f"Slide {slide_num}"
            slide_texts: List[str] = []

            # Check if slide has a title shape
            if slide.shapes.title and slide.shapes.title.text:
                slide_title = normalize_text(slide.shapes.title.text)

            # Process slide shapes
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        text = normalize_text(paragraph.text)
                        if text and text != slide_title:
                            slide_texts.append(text)

                elif shape.has_table:
                    tbl = shape.table
                    if tbl.rows:
                        headers = [normalize_text(cell.text) for cell in tbl.rows[0].cells]
                        rows = []
                        for row in tbl.rows[1:]:
                            rows.append([normalize_text(cell.text) for cell in row.cells])

                        md_lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
                        for r in rows:
                            md_lines.append("| " + " | ".join(r) + " |")
                        md_table = "\n".join(md_lines)

                        extracted_tables.append(
                            ExtractedTable(
                                headers=headers,
                                rows=rows,
                                markdown=md_table,
                                page_number=slide_num,
                                title=f"Table on Slide {slide_num} ({slide_title})",
                            )
                        )
                        slide_texts.append(md_table)

            # Notes
            try:
                if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
                    notes = normalize_text(slide.notes_slide.notes_text_frame.text)
                    if notes:
                        slide_texts.append(f"Speaker Notes: {notes}")
            except Exception as e:
                logger.debug(f"Notes read error on slide {slide_num}: {e}")

            if slide_texts:
                combined_slide_text = "\n\n".join(slide_texts)
                raw_text_parts.append(f"## {slide_title}\n{combined_slide_text}")

                content = format_chunk_with_context(
                    content=f"## {slide_title}\n{combined_slide_text}",
                    section_title=slide_title,
                    page_number=slide_num,
                )

                chunks.append(
                    ExtractedChunk(
                        content=content,
                        chunk_index=chunk_idx,
                        section_title=slide_title,
                        page_number=slide_num,
                        token_count=estimate_tokens(content),
                        metadata={"slide": slide_num, "title": slide_title, "type": "slide_content"},
                    )
                )
                chunk_idx += 1

        total_text = "\n\n".join(raw_text_parts)
        if not total_text.strip():
            raise CorruptFileError(
                "PPTX presentation contains no extractable text or content.",
                details={"filename": filename, "slide_count": slide_count},
            )

        return ExtractionResult(
            raw_text=total_text,
            chunks=chunks,
            tables=extracted_tables,
            metadata=extracted_metadata,
            page_count=slide_count,
            file_size_bytes=len(file_bytes),
        )

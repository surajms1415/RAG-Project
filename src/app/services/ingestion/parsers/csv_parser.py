import csv
import io
import logging
from typing import List
import pandas as pd

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


class CSVParser(BaseDocumentParser):
    """Extracts tabular structured data, schema, and rows from CSV files."""

    def extract(self, file_bytes: bytes, filename: str) -> ExtractionResult:
        # Decode byte stream
        try:
            content_str = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                content_str = file_bytes.decode("latin-1")
            except Exception as exc:
                raise CorruptFileError(f"Failed to decode CSV bytes: {exc}", details={"filename": filename})

        if not content_str.strip():
            raise CorruptFileError("CSV file is empty.", details={"filename": filename})

        # Detect delimiter
        try:
            sniffer = csv.Sniffer()
            sample = content_str[:4096]
            dialect = sniffer.sniff(sample)
            delimiter = dialect.delimiter
        except Exception:
            delimiter = ","

        try:
            df = pd.read_csv(io.StringIO(content_str), sep=delimiter)
        except Exception as exc:
            raise CorruptFileError(f"Failed to parse CSV data into dataframe: {exc}", details={"filename": filename, "error": str(exc)})

        if df.empty:
            raise CorruptFileError("CSV file has headers but 0 rows of data.", details={"filename": filename})

        row_count, col_count = df.shape
        headers = [str(c) for c in df.columns.tolist()]

        column_types = {col: str(dtype) for col, dtype in df.dtypes.items()}
        extracted_metadata = {
            "title": filename,
            "row_count": row_count,
            "column_count": col_count,
            "columns": headers,
            "column_types": column_types,
            "delimiter": delimiter,
        }

        # Convert to markdown table format
        # For large CSVs, summarize and chunk rows
        chunks: List[ExtractedChunk] = []
        extracted_tables: List[ExtractedTable] = []
        chunk_idx = 0

        # Summary chunk with schema and statistics
        summary_text = (
            f"Dataset Summary for {filename}:\n"
            f"- Total Rows: {row_count}\n"
            f"- Total Columns: {col_count}\n"
            f"- Columns and Types: {', '.join([f'{c} ({column_types[c]})' for c in headers])}\n"
        )
        content_summary = format_chunk_with_context(
            content=summary_text,
            section_title="Schema and Overview",
            page_number=1,
        )
        chunks.append(
            ExtractedChunk(
                content=content_summary,
                chunk_index=chunk_idx,
                section_title="Schema and Overview",
                page_number=1,
                token_count=estimate_tokens(content_summary),
                metadata={"type": "schema_summary", "columns": headers},
            )
        )
        chunk_idx += 1

        # Chunk the table rows in batches (e.g., 50 rows per chunk) for RAG context
        batch_size = 50
        for start_row in range(0, row_count, batch_size):
            end_row = min(start_row + batch_size, row_count)
            subset = df.iloc[start_row:end_row]

            md_table = subset.to_markdown(index=False)
            section_title = f"Rows {start_row + 1} to {end_row}"

            chunk_content = format_chunk_with_context(
                content=f"### {filename} ({section_title})\n{md_table}",
                section_title=section_title,
                page_number=1,
            )

            chunks.append(
                ExtractedChunk(
                    content=chunk_content,
                    chunk_index=chunk_idx,
                    section_title=section_title,
                    page_number=1,
                    token_count=estimate_tokens(chunk_content),
                    metadata={"row_range": [start_row + 1, end_row], "type": "table_batch"},
                )
            )
            chunk_idx += 1

        # Also store the first 100 rows in ExtractedTable
        preview_subset = df.head(100)
        extracted_tables.append(
            ExtractedTable(
                headers=headers,
                rows=[[str(val) for val in r] for r in preview_subset.values.tolist()],
                markdown=preview_subset.to_markdown(index=False),
                page_number=1,
                title=f"{filename} Tabular Data",
            )
        )

        raw_text = summary_text + "\n" + df.head(50).to_markdown(index=False)

        return ExtractionResult(
            raw_text=raw_text,
            chunks=chunks,
            tables=extracted_tables,
            metadata=extracted_metadata,
            page_count=1,
            file_size_bytes=len(file_bytes),
        )

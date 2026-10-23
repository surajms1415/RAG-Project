import re
import unicodedata
from typing import Optional


def normalize_text(text: str) -> str:
    """Cleans and standardizes extracted text with NFKC normalization and whitespace cleanup."""
    if not text:
        return ""

    # Unicode NFKC normalization
    normalized = unicodedata.normalize("NFKC", text)

    # Remove null bytes and non-printable control characters except newline and tab
    normalized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", normalized)

    # Standardize CRLF to LF
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")

    # Replace non-breaking spaces and other odd spaces with standard space
    normalized = re.sub(r"[\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]", " ", normalized)

    # Collapse multiple horizontal whitespace characters to a single space
    normalized = re.sub(r"[ \t]+", " ", normalized)

    # Collapse 3 or more consecutive newlines into 2 newlines (paragraph boundary)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)

    return normalized.strip()


def estimate_tokens(text: str) -> int:
    """Estimates token count for text using word count heuristics."""
    if not text:
        return 0
    words = len(text.split())
    # Standard heuristic: 1 word is approximately 1.33 tokens
    return max(1, int(words * 1.33))


def format_chunk_with_context(
    content: str,
    section_title: Optional[str] = None,
    page_number: Optional[int] = None,
) -> str:
    """Prepends breadcrumbs / metadata headers while preserving page and section references."""
    header_parts = []
    if section_title:
        header_parts.append(f"Section: {section_title}")
    if page_number is not None:
        header_parts.append(f"Page: {page_number}")

    if header_parts:
        header = f"[{' | '.join(header_parts)}]\n"
        return header + content
    return content

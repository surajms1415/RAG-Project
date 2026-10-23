import os
import zipfile
import io
from typing import Tuple
from src.app.core.config import get_settings
from src.app.core.exceptions import FileValidationError, CorruptFileError
from src.app.models.enums import FileType

settings = get_settings()

EXTENSION_TO_FILETYPE = {
    ".pdf": FileType.PDF,
    ".docx": FileType.DOCX,
    ".pptx": FileType.PPTX,
    ".csv": FileType.CSV,
}


def validate_file_metadata(filename: str, file_size: int) -> Tuple[str, FileType]:
    """Validates filename extension and size limits."""
    if not filename:
        raise FileValidationError("Filename cannot be empty")

    _, ext = os.path.splitext(filename.lower())
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"Unsupported file extension '{ext}'. Allowed extensions: {list(settings.ALLOWED_EXTENSIONS)}",
            details={"filename": filename, "extension": ext},
        )

    if file_size <= 0:
        raise FileValidationError(
            "Uploaded file is empty (0 bytes).",
            details={"filename": filename, "file_size": file_size},
        )

    if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise FileValidationError(
            f"File size ({file_size} bytes) exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_BYTES} bytes.",
            details={"filename": filename, "file_size": file_size, "max_allowed": settings.MAX_UPLOAD_SIZE_BYTES},
        )

    return ext, EXTENSION_TO_FILETYPE[ext]


def quick_integrity_check(file_bytes: bytes, file_type: FileType) -> None:
    """Performs fast header and structural validation before full parsing."""
    if len(file_bytes) == 0:
        raise FileValidationError("File content is completely empty.")

    if file_type == FileType.PDF:
        if not file_bytes.startswith(b"%PDF-"):
            raise CorruptFileError(
                "Invalid PDF header. File is corrupt or not a valid PDF.",
                details={"header_preview": str(file_bytes[:16])},
            )

    elif file_type in (FileType.DOCX, FileType.PPTX):
        # Must be valid zip archive
        if not file_bytes.startswith(b"PK\x03\x04"):
            raise CorruptFileError(
                f"Invalid archive header for {file_type.value.upper()}. File is corrupted.",
                details={"header_preview": str(file_bytes[:16])},
            )
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                names = z.namelist()
                if file_type == FileType.DOCX and "word/document.xml" not in names:
                    raise CorruptFileError(
                        "Corrupted DOCX: Missing word/document.xml",
                        details={"archive_contents": names[:10]},
                    )
                if file_type == FileType.PPTX and "ppt/presentation.xml" not in names:
                    raise CorruptFileError(
                        "Corrupted PPTX: Missing ppt/presentation.xml",
                        details={"archive_contents": names[:10]},
                    )
        except zipfile.BadZipFile as exc:
            raise CorruptFileError(
                f"Corrupted {file_type.value.upper()} archive: {exc}",
                details={"error": str(exc)},
            )

    elif file_type == FileType.CSV:
        # Check text decodability and that it's not all nulls
        try:
            sample = file_bytes[:4096].decode("utf-8")
        except UnicodeDecodeError:
            try:
                sample = file_bytes[:4096].decode("latin-1")
            except Exception as exc:
                raise CorruptFileError("Failed to decode CSV text", details={"error": str(exc)})

        if not sample.strip():
            raise FileValidationError("CSV file contains no text data.")

from typing import Any, Dict, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class DatabaseConnectionError(AppException):
    """Raised when the database connection or health check fails."""

    def __init__(self, message: str = "Database connection failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE, details=details)


class FileValidationError(AppException):
    """Raised when an uploaded document fails validation rules."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, status_code=status.HTTP_400_BAD_REQUEST, details=details)


class CorruptFileError(AppException):
    """Raised when file parsing fails due to corrupt or unreadable contents."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
            details=details,
        )


class DocumentNotFoundError(AppException):
    """Raised when a requested document is not found."""

    def __init__(self, document_id: str):
        super().__init__(
            message=f"Document with ID '{document_id}' not found",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"document_id": document_id},
        )


class IngestionJobError(AppException):
    """Raised during document ingestion failure."""

    def __init__(self, message: str, is_retryable: bool = False, details: Optional[Dict[str, Any]] = None):
        merged_details = details or {}
        merged_details["is_retryable"] = is_retryable
        super().__init__(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=merged_details,
        )
        self.is_retryable = is_retryable


def register_exception_handlers(app: FastAPI) -> None:
    """Registers standard exception handlers with FastAPI application."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "type": exc.__class__.__name__,
                    "message": exc.message,
                    "details": exc.details,
                    "path": request.url.path,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "type": "InternalServerError",
                    "message": "An unexpected error occurred processing your request.",
                    "details": {"error_repr": str(exc)},
                    "path": request.url.path,
                }
            },
        )

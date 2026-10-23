import hashlib
from typing import Optional
from sqlalchemy.orm import Session
from src.app.models.document import Document


def calculate_content_hash(data: bytes) -> str:
    """Calculates SHA-256 hash of byte content."""
    sha256 = hashlib.sha256()
    sha256.update(data)
    return sha256.hexdigest()


def find_document_by_hash(db: Session, content_hash: str) -> Optional[Document]:
    """Queries for an existing document with the given content hash."""
    return db.query(Document).filter(Document.content_hash == content_hash).first()

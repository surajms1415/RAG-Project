import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String
from src.app.core.database import Base


def generate_uuid() -> str:
    """Generates a stable UUIDv4 string."""
    return str(uuid.uuid4())


def utc_now() -> datetime:
    """Returns current UTC timestamp with timezone."""
    return datetime.now(timezone.utc)


class TimeStampedModel(Base):
    """Abstract base model adding stable UUID ID and UTC timestamp tracking."""

    __abstract__ = True

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

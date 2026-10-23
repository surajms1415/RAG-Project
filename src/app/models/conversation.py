from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    ForeignKey,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from src.app.models.base import TimeStampedModel
from src.app.models.enums import MessageRole


class Conversation(TimeStampedModel):
    """Represents a multi-turn chat session with the assistant."""

    __tablename__ = "conversations"

    title = Column(String(255), nullable=True)
    conversation_metadata = Column(JSON, nullable=True, default=dict)

    # Relationships
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at.asc()",
    )


class Message(TimeStampedModel):
    """Represents an individual message exchanged within a conversation."""

    __tablename__ = "messages"

    conversation_id = Column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role = Column(
        SQLEnum(MessageRole, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=MessageRole.USER,
    )
    content = Column(Text, nullable=False)
    citations = Column(JSON, nullable=True, default=list)
    token_count = Column(Integer, nullable=True)
    message_metadata = Column(JSON, nullable=True, default=dict)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

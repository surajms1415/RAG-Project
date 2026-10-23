from sqlalchemy import (
    Column,
    String,
    Text,
    JSON,
    DateTime,
    Enum as SQLEnum,
)
from src.app.models.base import TimeStampedModel
from src.app.models.enums import WorkflowStatus, WorkflowType


class WorkflowExecution(TimeStampedModel):
    """Tracks asynchronous and automated workflow executions (ingestion, n8n orchestrations, analytics)."""

    __tablename__ = "workflow_executions"

    workflow_type = Column(String(100), nullable=False, index=True)
    status = Column(
        SQLEnum(WorkflowStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=WorkflowStatus.PENDING,
        index=True,
    )
    input_payload = Column(JSON, nullable=False, default=dict)
    output_payload = Column(JSON, nullable=True, default=dict)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

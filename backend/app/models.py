"""Database models for orchestrator."""

from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    JSON,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
import enum

from app.core.db import Base

try:
    from sqlalchemy.dialects.postgresql import VECTOR
except ImportError:
    # Fallback for environments without pgvector
    VECTOR = None  # type: ignore


class JobStatus(str, enum.Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionMode(str, enum.Enum):
    """Orchestrator execution mode."""
    FLOW = "flow"
    MCP = "mcp"
    AGENT = "agent"
    AUTO = "auto"


class MemoryItem(Base):
    """Memory storage with vector embeddings."""
    __tablename__ = "memory_items"
    
    id = Column(String, primary_key=True)  # SHA256-based ID for idempotency
    text = Column(Text, nullable=False)
    tags = Column(ARRAY(String), default=[], nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    speaker_id = Column(String, nullable=True)
    # sentence-transformers/all-MiniLM-L6-v2 (384 dimensions)
    embedding = Column(
        VECTOR(384) if VECTOR else Text,
        nullable=True
    )
    
    def __repr__(self):
        return f"<MemoryItem(id={self.id[:8]}..., tags={self.tags})>"


class Job(Base):
    """Orchestrator job tracking."""
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True)  # SHA256-based ID for idempotency
    intent = Column(String, nullable=False, index=True)
    mode = Column(SQLEnum(ExecutionMode), nullable=False)
    status = Column(
        SQLEnum(JobStatus),
        nullable=False,
        default=JobStatus.PENDING,
        index=True
    )
    
    # Input/output
    inputs = Column(JSON, nullable=False)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    callback_url = Column(String, nullable=True)
    metadata = Column(JSON, default={}, nullable=False)
    
    def __repr__(self):
        job_id = self.id[:8] if self.id else "None"
        return (
            f"<Job(id={job_id}..., "
            f"intent={self.intent}, status={self.status})>"
        )
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate job duration if completed."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

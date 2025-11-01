"""Memory service schemas for request/response validation."""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class MemoryWriteIn(BaseModel):
    """Input schema for writing memory items."""
    text: str = Field(..., min_length=1, max_length=10000, description="Memory text content")
    tags: List[str] = Field(default_factory=list, description="Associated tags")
    speaker_id: Optional[str] = Field(None, description="ID of the speaker/author")
    ts_iso: Optional[str] = Field(None, description="ISO timestamp (optional)")


class MemorySearchIn(BaseModel):
    """Input schema for searching memory items."""
    query: str = Field(..., min_length=1, description="Search query text")
    since: Optional[str] = Field(None, description="Filter memories since this ISO timestamp")
    until: Optional[str] = Field(None, description="Filter memories until this ISO timestamp")
    tags: List[str] = Field(default_factory=list, description="Filter by tags")
    top_k: int = Field(default=10, ge=1, le=100, description="Maximum number of results")


class MemoryHit(BaseModel):
    """A single memory search result."""
    id: int = Field(..., description="Memory item ID")
    text: str = Field(..., description="Memory text content")
    score: float = Field(..., description="Relevance score")
    tags: List[str] = Field(..., description="Associated tags")
    ts_iso: Optional[str] = Field(None, description="ISO timestamp when created")
    speaker_id: Optional[str] = Field(None, description="Speaker/author ID")


class MemorySearchOut(BaseModel):
    """Output schema for memory search results."""
    hits: List[MemoryHit] = Field(..., description="Search result hits")
    total_found: int = Field(..., description="Total number of matches")
    query: str = Field(..., description="The original search query")
    search_time_ms: float = Field(..., description="Search execution time in milliseconds")


class MemoryWriteOut(BaseModel):
    """Output schema for memory write operations."""
    id: int = Field(..., description="ID of the created memory item")
    text: str = Field(..., description="The stored text")
    tags: List[str] = Field(..., description="Associated tags")
    ts_iso: str = Field(..., description="ISO timestamp when created")
    speaker_id: Optional[str] = Field(None, description="Speaker/author ID")
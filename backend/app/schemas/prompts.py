"""Prompt template management schemas."""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class PromptRegisterIn(BaseModel):
    """Prompt registration request."""
    template: str = Field(..., description="Prompt template text")
    role: str = Field(..., description="Role (system, user, assistant)")
    tags: List[str] = Field(default_factory=list, description="Tags")
    description: Optional[str] = Field(
        None,
        description="Description of prompt"
    )


class PromptOut(BaseModel):
    """Prompt details response."""
    id: int
    template: str
    role: str
    tags: List[str]
    description: Optional[str]
    success_count: int = 0
    fail_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime]


class PromptStatsUpdate(BaseModel):
    """Prompt statistics update request."""
    prompt_id: int
    success: bool = Field(..., description="Whether prompt was successful")


class PromptSearchIn(BaseModel):
    """Prompt search request."""
    role: Optional[str] = None
    tags: Optional[List[str]] = None
    min_success_rate: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum success rate (0.0-1.0)"
    )

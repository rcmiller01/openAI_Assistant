"""Interaction feedback collection schemas."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class FeedbackIn(BaseModel):
    """Feedback submission request."""
    interaction_id: str = Field(
        ...,
        description="Unique interaction identifier"
    )
    auto_grade: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Automated quality score (0.0-1.0)"
    )
    human_grade: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Human quality score (0.0-1.0)"
    )
    human_comment: Optional[str] = Field(
        None,
        description="Human feedback comment"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata"
    )


class FeedbackOut(BaseModel):
    """Feedback details response."""
    id: int
    interaction_id: str
    auto_grade: Optional[float]
    human_grade: Optional[float]
    human_comment: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: Optional[datetime]


class FeedbackStatsOut(BaseModel):
    """Feedback statistics response."""
    total_feedback: int
    avg_auto_grade: Optional[float]
    avg_human_grade: Optional[float]
    human_graded_count: int

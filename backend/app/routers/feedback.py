"""Interaction feedback collection endpoints."""

from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import AuthenticatedUser
from app.deps.db import get_async_db
from app.schemas.feedback import (
    FeedbackIn,
    FeedbackOut,
    FeedbackStatsOut,
)

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/", response_model=FeedbackOut)
async def submit_feedback(
    data: FeedbackIn,
    _token: AuthenticatedUser,
    db: AsyncSession = Depends(get_async_db),
) -> FeedbackOut:
    """
    Submit interaction feedback.
    
    - Accepts auto-grade, human-grade, and comments
    - Links to interaction_id
    - Updates existing feedback if interaction_id exists
    """
    # TODO: Implement DB upsert
    # 1. Check if feedback exists for interaction_id
    # 2. Update if exists, insert if new
    # 3. Return FeedbackOut
    raise HTTPException(
        status_code=501,
        detail="Feedback submission not yet implemented",
    )


@router.get("/interaction/{interaction_id}", response_model=FeedbackOut)
async def get_feedback_by_interaction(
    interaction_id: str,
    _token: AuthenticatedUser,
    db: AsyncSession = Depends(get_async_db),
) -> FeedbackOut:
    """Get feedback for specific interaction."""
    # TODO: Implement DB query
    raise HTTPException(
        status_code=404,
        detail=f"Feedback for interaction {interaction_id} not found",
    )


@router.get("/stats", response_model=FeedbackStatsOut)
async def get_feedback_stats(
    _token: AuthenticatedUser,
    db: AsyncSession = Depends(get_async_db),
) -> FeedbackStatsOut:
    """
    Get aggregate feedback statistics.
    
    - Total feedback count
    - Average auto-grade and human-grade
    - Human grading participation rate
    """
    # TODO: Implement DB aggregation
    # 1. Count total feedback records
    # 2. Calculate AVG(auto_grade) and AVG(human_grade)
    # 3. Count records with non-null human_grade
    # 4. Return stats
    return FeedbackStatsOut(
        total_feedback=0,
        avg_auto_grade=None,
        avg_human_grade=None,
        human_graded_count=0,
    )


@router.get("/", response_model=List[FeedbackOut])
async def list_feedback(
    limit: int = 50,
    offset: int = 0,
    _token: AuthenticatedUser = None,
    db: AsyncSession = Depends(get_async_db),
) -> List[FeedbackOut]:
    """List recent feedback with pagination."""
    # TODO: Implement DB query with pagination
    return []

"""Common schemas for error handling and responses."""

from typing import Any, Dict, Optional
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class SuccessResponse(BaseModel):
    """Standard success response format."""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    version: str
    database: str
    redis: Optional[str] = None


class VersionResponse(BaseModel):
    """Version information response."""
    version: str
    environment: str
    api_version: str = "v1"


class DryRunResponse(BaseModel):
    """Dry run operation response."""
    dry_run: bool = True
    operation: str
    would_affect: Dict[str, Any]
    confirmation_required: bool = True
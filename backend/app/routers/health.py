"""Health and version check endpoints."""

import os
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter
from app.schemas.common import HealthResponse, VersionResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])

APP_VERSION = os.getenv("APP_VERSION", "dev")
APP_ENV = os.getenv("APP_ENV", "dev")


@router.get("/", response_model=Dict[str, Any])
async def root() -> Dict[str, Any]:
    """Root endpoint with API status."""
    return {
        "service": "OpenAI Personal Assistant API",
        "version": APP_VERSION,
        "environment": APP_ENV,
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/healthz", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    # TODO: Add actual database connectivity check
    database_status = "connected"  # Placeholder
    redis_status = None  # Placeholder
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version=APP_VERSION,
        database=database_status,
        redis=redis_status
    )


@router.get("/version", response_model=VersionResponse)
async def version_info() -> VersionResponse:
    """Version information endpoint."""
    return VersionResponse(
        version=APP_VERSION,
        environment=APP_ENV
    )

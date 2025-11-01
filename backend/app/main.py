"""Main FastAPI application for OpenAI Personal Assistant."""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.db import setup_pgvector, cleanup_database
from app.core.scheduler import start_scheduler, stop_scheduler
from app.routers import memory, health, fs, fetch, ssh, agents, prompts, feedback
from app.schemas.common import ErrorResponse

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Application metadata
APP_VERSION = "0.1.0"
APP_ENV = os.getenv("APP_ENV", "dev")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    # Startup
    logger.info("Starting OpenAI Personal Assistant API...")
    
    try:
        # Initialize database and pgvector
        await setup_pgvector()
        logger.info("Database initialized")
        
        # Start scheduler
        start_scheduler()
        logger.info("Scheduler started")
        
        yield
        
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down...")
        stop_scheduler()
        await cleanup_database()
        logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="OpenAI Personal Assistant API",
    description="Private extensible personal assistant environment",
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs" if APP_ENV == "dev" else None,
    redoc_url="/redoc" if APP_ENV == "dev" else None,
)

# CORS configuration
cors_origins = os.getenv("CORS_ORIGINS", "").split(",")
if cors_origins and cors_origins[0]:  # Only add CORS if origins are specified
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    logger.info(f"CORS enabled for origins: {cors_origins}")


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail="An unexpected error occurred"
        ).dict()
    )


# Mount routers
app.include_router(health.router)  # Health endpoints at root
app.include_router(memory.router, prefix="/api/v1")
app.include_router(fs.router, prefix="/api/v1")
app.include_router(fetch.router, prefix="/api/v1")
app.include_router(ssh.router, prefix="/api/v1")
app.include_router(agents.router, prefix="/api/v1")
app.include_router(prompts.router, prefix="/api/v1")
app.include_router(feedback.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("APP_HOST", "0.0.0.0")
    port = int(os.getenv("APP_PORT", "8080"))
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=APP_ENV == "dev",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
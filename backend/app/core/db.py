"""Database configuration and session management."""

import os
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Database configuration from environment
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "opa")
POSTGRES_USER = os.getenv("POSTGRES_USER", "opa")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "opa_password")

DATABASE_URL = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("APP_ENV") == "dev",
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base model for all database entities."""
    pass


# Import models after Base is defined to avoid circular imports
# Models are imported at module level for SQLAlchemy to discover them
try:
    from app.models import MemoryItem, Job  # noqa: F401
except ImportError:
    logger.warning("Could not import models - running without database?")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def setup_pgvector() -> None:
    """Initialize pgvector extension and create tables."""
    async with engine.begin() as conn:
        try:
            # Enable pgvector extension
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            logger.info("pgvector extension enabled")
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created")
            
        except Exception as e:
            logger.error(f"Failed to setup pgvector: {e}")
            raise


async def cleanup_database() -> None:
    """Clean up database connections."""
    await engine.dispose()
    logger.info("Database connections cleaned up")

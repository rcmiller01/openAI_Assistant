"""Database configuration and session management."""

import os
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text, Column, Integer, String, Text, DateTime, ARRAY
from sqlalchemy.dialects.postgresql import VECTOR
from sqlalchemy.sql import func

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


class MemoryItem(Base):
    """Memory storage table with vector support."""
    __tablename__ = "memory_items"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    tags = Column(ARRAY(String), default=[], nullable=False)
    ts = Column(DateTime(timezone=True), server_default=func.now())
    speaker_id = Column(String, nullable=True)
    embedding = Column(VECTOR(384), nullable=True)  # Placeholder dimension


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
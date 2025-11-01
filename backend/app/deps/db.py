"""Database session dependency."""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import async_session_maker


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides async database session."""
    async with async_session_maker() as session:
        yield session

"""Memory service router with BM25 + vector hybrid search."""

import hashlib
import logging
import time
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, text
from sqlalchemy.sql import func

from app.core.db import get_session, MemoryItem
from app.deps.auth import AuthenticatedUser
from app.schemas.memory import (
    MemoryWriteIn, MemoryWriteOut, MemorySearchIn, MemorySearchOut, MemoryHit
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/memory", tags=["memory"])


def generate_placeholder_embedding(text: str) -> List[float]:
    """
    Generate a placeholder embedding vector from text.
    
    This is a simple hash-based approach for development.
    TODO: Replace with real embeddings (Ollama, OpenAI, etc.)
    
    Args:
        text: Input text to embed
        
    Returns:
        List[float]: 384-dimensional vector
    """
    # Create hash from text
    hash_obj = hashlib.sha256(text.encode())
    hash_bytes = hash_obj.digest()
    
    # Convert to 384-dimensional vector
    vector = []
    for i in range(384):
        # Use modular arithmetic to create pseudo-random but deterministic values
        val = (hash_bytes[i % len(hash_bytes)] + i) % 256
        # Normalize to [-1, 1] range
        normalized = (val / 127.5) - 1.0
        vector.append(normalized)
    
    return vector


@router.post("/write", response_model=MemoryWriteOut)
async def write_memory(
    memory_data: MemoryWriteIn,
    session: AsyncSession = Depends(get_session),
    _: AuthenticatedUser = Depends()
) -> MemoryWriteOut:
    """
    Write a new memory item to the database.
    
    Args:
        memory_data: Memory content and metadata
        session: Database session
        
    Returns:
        MemoryWriteOut: Created memory item details
    """
    try:
        # Parse timestamp if provided
        ts = None
        if memory_data.ts_iso:
            try:
                ts = datetime.fromisoformat(memory_data.ts_iso.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid timestamp format. Use ISO 8601."
                )
        
        # Generate embedding
        embedding = generate_placeholder_embedding(memory_data.text)
        
        # Create memory item
        memory_item = MemoryItem(
            text=memory_data.text,
            tags=memory_data.tags,
            speaker_id=memory_data.speaker_id,
            ts=ts,
            embedding=embedding
        )
        
        session.add(memory_item)
        await session.commit()
        await session.refresh(memory_item)
        
        logger.info(f"Created memory item {memory_item.id}")
        
        return MemoryWriteOut(
            id=memory_item.id,
            text=memory_item.text,
            tags=memory_item.tags,
            ts_iso=memory_item.ts.isoformat() if memory_item.ts else datetime.utcnow().isoformat(),
            speaker_id=memory_item.speaker_id
        )
        
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to write memory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to write memory item"
        )


@router.post("/search", response_model=MemorySearchOut)
async def search_memory(
    search_data: MemorySearchIn,
    session: AsyncSession = Depends(get_session),
    _: AuthenticatedUser = Depends()
) -> MemorySearchOut:
    """
    Search memory items using hybrid BM25 + vector search.
    
    Args:
        search_data: Search parameters
        session: Database session
        
    Returns:
        MemorySearchOut: Search results with relevance scores
    """
    start_time = time.time()
    
    try:
        # Build base query
        query = select(MemoryItem)
        
        # Apply filters
        filters = []
        
        # Time range filters
        if search_data.since:
            try:
                since_dt = datetime.fromisoformat(search_data.since.replace('Z', '+00:00'))
                filters.append(MemoryItem.ts >= since_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid 'since' timestamp format"
                )
        
        if search_data.until:
            try:
                until_dt = datetime.fromisoformat(search_data.until.replace('Z', '+00:00'))
                filters.append(MemoryItem.ts <= until_dt)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid 'until' timestamp format"
                )
        
        # Tag filters
        if search_data.tags:
            # Match any of the provided tags
            tag_conditions = [MemoryItem.tags.contains([tag]) for tag in search_data.tags]
            filters.append(or_(*tag_conditions))
        
        # Apply all filters
        if filters:
            query = query.where(and_(*filters))
        
        # For now, do simple text search (placeholder for BM25)
        # TODO: Implement proper BM25 search with PostgreSQL full-text search
        if search_data.query.strip():
            query = query.where(
                MemoryItem.text.ilike(f"%{search_data.query}%")
            )
        
        # Generate query embedding for vector similarity
        query_embedding = generate_placeholder_embedding(search_data.query)
        
        # Execute query
        result = await session.execute(query.limit(search_data.top_k))
        items = result.scalars().all()
        
        # Calculate hybrid scores (placeholder implementation)
        hits = []
        for item in items:
            # Simple text-based relevance score (placeholder for BM25)
            text_score = len([word for word in search_data.query.lower().split() 
                            if word in item.text.lower()]) / max(len(search_data.query.split()), 1)
            
            # Simple vector similarity (placeholder)
            # In real implementation, use cosine similarity with pgvector
            vector_score = 0.5  # Placeholder
            
            # Combine scores (weighted average)
            combined_score = (text_score * 0.7) + (vector_score * 0.3)
            
            hits.append(MemoryHit(
                id=item.id,
                text=item.text,
                score=combined_score,
                tags=item.tags,
                ts_iso=item.ts.isoformat() if item.ts else None,
                speaker_id=item.speaker_id
            ))
        
        # Sort by score descending
        hits.sort(key=lambda x: x.score, reverse=True)
        
        search_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        logger.info(f"Memory search completed: {len(hits)} results in {search_time:.2f}ms")
        
        return MemorySearchOut(
            hits=hits,
            total_found=len(hits),
            query=search_data.query,
            search_time_ms=search_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Memory search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Memory search failed"
        )
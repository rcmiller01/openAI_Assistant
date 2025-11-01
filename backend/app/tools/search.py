"""Hybrid search combining BM25 keyword + vector semantic search."""

import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MemoryItem
from app.tools.embedding import generate_embedding

logger = logging.getLogger(__name__)

# Configuration
DEFAULT_K = int(os.getenv("SEARCH_DEFAULT_K", "10"))
DEFAULT_BM25_WEIGHT = float(os.getenv("SEARCH_BM25_WEIGHT", "0.5"))
DEFAULT_VECTOR_WEIGHT = float(os.getenv("SEARCH_VECTOR_WEIGHT", "0.5"))


@dataclass
class SearchResult:
    """Search result with scores."""
    id: str
    text: str
    tags: List[str]
    created_at: str
    bm25_score: Optional[float] = None
    vector_score: Optional[float] = None
    combined_score: float = 0.0


async def hybrid_search(
    session: AsyncSession,
    query_text: str,
    query_tags: Optional[List[str]] = None,
    k: int = DEFAULT_K,
    bm25_weight: float = DEFAULT_BM25_WEIGHT,
    vector_weight: float = DEFAULT_VECTOR_WEIGHT,
) -> List[SearchResult]:
    """
    Perform hybrid search using BM25 + vector similarity.
    
    Args:
        session: Database session
        query_text: Search query text
        query_tags: Optional tag filter
        k: Number of results to return
        bm25_weight: Weight for BM25 score (0-1)
        vector_weight: Weight for vector score (0-1)
        
    Returns:
        List of SearchResult objects sorted by combined score
    """
    # Generate query embedding
    query_embedding = await generate_embedding(query_text)
    
    # Build query using SQL function from migrations
    query = text("""
        SELECT 
            id, 
            text, 
            tags, 
            created_at,
            bm25_score,
            vector_score,
            combined_score
        FROM hybrid_search(
            :query_text,
            :query_embedding::vector(384),
            :query_tags::text[],
            :k,
            :bm25_weight,
            :vector_weight
        )
    """)
    
    params = {
        "query_text": query_text,
        "query_embedding": str(query_embedding),
        "query_tags": query_tags or [],
        "k": k,
        "bm25_weight": bm25_weight,
        "vector_weight": vector_weight,
    }
    
    result = await session.execute(query, params)
    rows = result.fetchall()
    
    results = [
        SearchResult(
            id=row[0],
            text=row[1],
            tags=row[2],
            created_at=row[3].isoformat() if row[3] else "",
            bm25_score=row[4],
            vector_score=row[5],
            combined_score=row[6],
        )
        for row in rows
    ]
    
    logger.info(
        f"Hybrid search returned {len(results)} results",
        extra={
            "query": query_text[:50],
            "tags": query_tags,
            "k": k,
            "bm25_weight": bm25_weight,
            "vector_weight": vector_weight,
        }
    )
    
    return results


async def vector_search(
    session: AsyncSession,
    query_text: str,
    query_tags: Optional[List[str]] = None,
    k: int = DEFAULT_K,
) -> List[SearchResult]:
    """
    Perform pure vector similarity search.
    Faster than hybrid search for semantic queries.
    
    Args:
        session: Database session
        query_text: Search query text
        query_tags: Optional tag filter
        k: Number of results to return
        
    Returns:
        List of SearchResult objects sorted by similarity
    """
    query_embedding = await generate_embedding(query_text)
    
    query = text("""
        SELECT 
            id, 
            text, 
            tags, 
            created_at,
            similarity
        FROM vector_search(
            :query_embedding::vector(384),
            :query_tags::text[],
            :k
        )
    """)
    
    params = {
        "query_embedding": str(query_embedding),
        "query_tags": query_tags or [],
        "k": k,
    }
    
    result = await session.execute(query, params)
    rows = result.fetchall()
    
    results = [
        SearchResult(
            id=row[0],
            text=row[1],
            tags=row[2],
            created_at=row[3].isoformat() if row[3] else "",
            vector_score=row[4],
            combined_score=row[4],
        )
        for row in rows
    ]
    
    logger.info(
        f"Vector search returned {len(results)} results",
        extra={"query": query_text[:50], "tags": query_tags, "k": k}
    )
    
    return results


async def bm25_search(
    session: AsyncSession,
    query_text: str,
    query_tags: Optional[List[str]] = None,
    k: int = DEFAULT_K,
) -> List[SearchResult]:
    """
    Perform pure BM25 keyword search.
    Faster than hybrid search for exact keyword matches.
    
    Args:
        session: Database session
        query_text: Search query text
        query_tags: Optional tag filter
        k: Number of results to return
        
    Returns:
        List of SearchResult objects sorted by BM25 score
    """
    query = text("""
        SELECT 
            id, 
            text, 
            tags, 
            created_at,
            score
        FROM bm25_search(
            :query_text,
            :query_tags::text[],
            :k
        )
    """)
    
    params = {
        "query_text": query_text,
        "query_tags": query_tags or [],
        "k": k,
    }
    
    result = await session.execute(query, params)
    rows = result.fetchall()
    
    results = [
        SearchResult(
            id=row[0],
            text=row[1],
            tags=row[2],
            created_at=row[3].isoformat() if row[3] else "",
            bm25_score=row[4],
            combined_score=row[4],
        )
        for row in rows
    ]
    
    logger.info(
        f"BM25 search returned {len(results)} results",
        extra={"query": query_text[:50], "tags": query_tags, "k": k}
    )
    
    return results


async def simple_keyword_search(
    session: AsyncSession,
    query_text: str,
    query_tags: Optional[List[str]] = None,
    k: int = DEFAULT_K,
) -> List[SearchResult]:
    """
    Simple keyword search using SQLAlchemy (no SQL functions required).
    Fallback when database functions are not available.
    
    Args:
        session: Database session
        query_text: Search query text
        query_tags: Optional tag filter
        k: Number of results to return
        
    Returns:
        List of SearchResult objects
    """
    query = select(MemoryItem)
    
    # Add filters
    if query_text:
        query = query.where(
            MemoryItem.text.ilike(f"%{query_text}%")
        )
    
    if query_tags:
        query = query.where(
            MemoryItem.tags.overlap(query_tags)
        )
    
    query = query.order_by(MemoryItem.created_at.desc()).limit(k)
    
    result = await session.execute(query)
    rows = result.scalars().all()
    
    results = [
        SearchResult(
            id=row.id,
            text=row.text,
            tags=row.tags,
            created_at=row.created_at.isoformat() if row.created_at else "",
            combined_score=1.0,  # No scoring in simple search
        )
        for row in rows
    ]
    
    logger.info(
        f"Simple keyword search returned {len(results)} results",
        extra={"query": query_text[:50], "tags": query_tags, "k": k}
    )
    
    return results


async def search_memories(
    session: AsyncSession,
    query: str,
    tags: Optional[List[str]] = None,
    k: int = DEFAULT_K,
    mode: str = "hybrid",
    bm25_weight: float = DEFAULT_BM25_WEIGHT,
    vector_weight: float = DEFAULT_VECTOR_WEIGHT,
) -> Dict[str, Any]:
    """
    Unified search interface with multiple modes.
    
    Args:
        session: Database session
        query: Search query text
        tags: Optional tag filter
        k: Number of results to return
        mode: Search mode ('hybrid', 'vector', 'bm25', 'simple')
        bm25_weight: BM25 weight for hybrid mode
        vector_weight: Vector weight for hybrid mode
        
    Returns:
        Dict with items, total_items, and mode
    """
    try:
        if mode == "hybrid":
            results = await hybrid_search(
                session, query, tags, k, bm25_weight, vector_weight
            )
        elif mode == "vector":
            results = await vector_search(session, query, tags, k)
        elif mode == "bm25":
            results = await bm25_search(session, query, tags, k)
        else:  # simple or fallback
            results = await simple_keyword_search(session, query, tags, k)
        
        return {
            "items": [
                {
                    "id": r.id,
                    "text": r.text,
                    "tags": r.tags,
                    "created_at": r.created_at,
                    "bm25_score": r.bm25_score,
                    "vector_score": r.vector_score,
                    "combined_score": r.combined_score,
                }
                for r in results
            ],
            "total_items": len(results),
            "mode": mode,
            "query": query,
        }
    
    except Exception as e:
        logger.error(f"Search failed: {e}", extra={"mode": mode})
        # Fallback to simple search on error
        if mode != "simple":
            logger.info("Falling back to simple keyword search")
            return await search_memories(
                session, query, tags, k, mode="simple"
            )
        raise

"""
Memory tools - Pure functions for memory operations.

Can be called from FastAPI orchestrator or n8n workflows.
Handles vector embeddings and hybrid BM25 + vector search.
"""

from typing import Dict, Any, List, Optional
import logging
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

# In-memory store fallback (used when DB not available)
_memory_store: Dict[str, Dict[str, Any]] = {}

# Flag to track if DB is available
_use_database = False


def _get_memory_id(text: str, tags: Optional[List[str]] = None) -> str:
    """Generate stable ID for memory item."""
    content = f"{text}{''.join(sorted(tags or []))}"
    return hashlib.sha256(content.encode()).hexdigest()


async def store_memory(
    text: str,
    tags: Optional[List[str]] = None,
    speaker_id: Optional[str] = None,
    session: Optional[Any] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Store memory item with vector embedding.
    
    Pure function that stores text, generates embeddings,
    and returns item metadata.
    
    Args:
        text: Text content to store
        tags: Optional tags for categorization
        speaker_id: Optional speaker identifier
        session: Optional DB session (if provided, uses DB)
        
    Returns:
        Dictionary with item_id and status
    """
    item_id = _get_memory_id(text, tags)
    created_at = datetime.utcnow()
    
    # Try database storage if session provided
    if session:
        try:
            from app.models import MemoryItem
            from app.tools.embedding import generate_embedding
            
            # Generate embedding
            embedding = await generate_embedding(text)
            
            # Create and store memory item
            memory = MemoryItem(
                id=item_id,
                text=text,
                tags=tags or [],
                speaker_id=speaker_id,
                embedding=embedding,
            )
            
            session.add(memory)
            await session.commit()
            await session.refresh(memory)
            
            logger.info(
                f"Stored memory in DB: {item_id[:12]}...",
                extra={"item_id": item_id, "tags": tags}
            )
            
            return {
                "item_id": item_id,
                "status": "stored",
                "storage": "database",
                "text_length": len(text),
                "tags": tags or [],
                "created_at": memory.created_at.isoformat(),
            }
            
        except Exception as e:
            logger.warning(
                f"Database storage failed: {e}. Falling back to memory."
            )
    
    # Fallback: In-memory storage
    _memory_store[item_id] = {
        "id": item_id,
        "text": text,
        "tags": tags or [],
        "speaker_id": speaker_id,
        "created_at": created_at.isoformat(),
        "embedding": None
    }
    
    logger.info(
        f"Stored memory in-memory: {item_id[:12]}...",
        extra={"item_id": item_id, "tags": tags}
    )
    
    return {
        "item_id": item_id,
        "status": "stored",
        "storage": "memory",
        "text_length": len(text),
        "tags": tags or [],
        "created_at": created_at.isoformat()
    }


async def search_memory(
    query: str,
    k: int = 5,
    tags: Optional[List[str]] = None,
    session: Optional[Any] = None,
    mode: str = "hybrid",
    **kwargs
) -> Dict[str, Any]:
    """
    Search memory using hybrid BM25 + vector search.
    
    Pure function that performs semantic + keyword search
    over stored memories.
    
    Args:
        query: Search query
        k: Number of results to return
        tags: Optional tag filter
        session: Optional DB session (if provided, uses DB search)
        mode: Search mode ('hybrid', 'vector', 'bm25', 'simple')
        
    Returns:
        Dictionary with results and metadata
    """
    # Try database search if session provided
    if session:
        try:
            from app.tools.search import search_memories
            
            results = await search_memories(
                session=session,
                query=query,
                tags=tags,
                k=k,
                mode=mode
            )
            
            logger.info(
                f"DB search: '{query[:50]}' found {results['total_items']}",
                extra={"mode": mode, "count": results['total_items']}
            )
            
            return {
                **results,
                "storage": "database"
            }
            
        except Exception as e:
            logger.warning(
                f"Database search failed: {e}. Falling back to memory."
            )
    
    # Fallback: In-memory search
    filtered_items = []
    for item_id, item in _memory_store.items():
        if tags:
            if not any(tag in item.get("tags", []) for tag in tags):
                continue
        filtered_items.append(item)
    
    # Simple keyword search
    results = []
    query_lower = query.lower()
    for item in filtered_items:
        text_lower = item["text"].lower()
        if query_lower in text_lower:
            # Simple relevance score
            words = text_lower.split()
            score = text_lower.count(query_lower) / len(words) if words else 0
            results.append({
                "id": item["id"],
                "text": item["text"],
                "tags": item.get("tags", []),
                "score": round(score, 4),
                "created_at": item.get("created_at")
            })
    
    # Sort by score and limit
    results.sort(key=lambda x: x["score"], reverse=True)
    results = results[:k]
    
    logger.info(
        f"In-memory search: '{query[:50]}' found {len(results)}",
        extra={"query": query, "count": len(results), "tags": tags}
    )
    
    return {
        "query": query,
        "items": results,
        "total_items": len(results),
        "mode": "simple",
        "storage": "memory"
    }


async def list_memories(
    limit: int = 50,
    offset: int = 0,
    tags: Optional[List[str]] = None,
    session: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    List all memories with optional filtering.
    
    Args:
        limit: Max items to return
        offset: Skip this many items
        tags: Optional tag filter
        session: Optional DB session (if provided, uses DB)
        
    Returns:
        Dictionary with items and pagination
    """
    # Try database listing if session provided
    if session:
        try:
            from sqlalchemy import select
            from app.models import MemoryItem
            
            query = select(MemoryItem)
            
            if tags:
                query = query.where(MemoryItem.tags.overlap(tags))
            
            query = query.order_by(
                MemoryItem.created_at.desc()
            ).offset(offset).limit(limit)
            
            result = await session.execute(query)
            items = result.scalars().all()
            
            # Get total count
            count_query = select(MemoryItem)
            if tags:
                count_query = count_query.where(
                    MemoryItem.tags.overlap(tags)
                )
            total_result = await session.execute(count_query)
            total = len(total_result.scalars().all())
            
            return {
                "items": [
                    {
                        "id": item.id,
                        "text": item.text,
                        "tags": item.tags,
                        "created_at": item.created_at.isoformat(),
                        "speaker_id": item.speaker_id,
                    }
                    for item in items
                ],
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total,
                "storage": "database"
            }
            
        except Exception as e:
            logger.warning(
                f"Database list failed: {e}. Falling back to memory."
            )
    
    # Fallback: In-memory listing
    items = list(_memory_store.values())
    
    # Filter by tags
    if tags:
        items = [
            item for item in items
            if any(tag in item.get("tags", []) for tag in tags)
        ]
    
    # Sort by created_at descending
    items.sort(
        key=lambda x: x.get("created_at", ""),
        reverse=True
    )
    
    # Paginate
    total = len(items)
    items = items[offset:offset + limit]
    
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "has_more": offset + limit < total,
        "storage": "memory"
    }


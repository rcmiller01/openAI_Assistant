"""Embedding generation with retry/backoff for memory search."""

import os
import logging
from typing import List, Optional
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)

# Configuration
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2"
)
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "384"))
MAX_RETRIES = int(os.getenv("EMBEDDING_MAX_RETRIES", "3"))
BASE_DELAY = float(os.getenv("EMBEDDING_BASE_DELAY", "1.0"))
MAX_DELAY = float(os.getenv("EMBEDDING_MAX_DELAY", "60.0"))


def retry_with_backoff(max_retries: int = MAX_RETRIES):
    """Decorator for exponential backoff retry logic."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = BASE_DELAY
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        # Exponential backoff with jitter
                        jitter = delay * 0.1
                        actual_delay = min(
                            delay + (jitter * (2 * asyncio.get_event_loop().time() % 1 - 1)),
                            MAX_DELAY
                        )
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                            f"Retrying in {actual_delay:.2f}s..."
                        )
                        await asyncio.sleep(actual_delay)
                        delay *= 2  # Exponential backoff
                    else:
                        logger.error(
                            f"All {max_retries} attempts failed for {func.__name__}"
                        )
            
            raise last_exception  # type: ignore
        
        return wrapper
    return decorator


@retry_with_backoff()
async def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for text using configured model.
    
    Args:
        text: Text to embed
        
    Returns:
        List of floats representing the embedding vector
        
    Raises:
        Exception: If embedding generation fails after all retries
    """
    try:
        # Try to use sentence-transformers if available
        from sentence_transformers import SentenceTransformer
        
        # Load model (cached after first load)
        model = SentenceTransformer(EMBEDDING_MODEL)
        
        # Generate embedding
        embedding = model.encode(text, convert_to_numpy=True)
        
        logger.info(
            f"Generated embedding for text (length: {len(text)})",
            extra={"model": EMBEDDING_MODEL, "dimensions": len(embedding)}
        )
        
        return embedding.tolist()
        
    except ImportError:
        logger.warning(
            "sentence-transformers not available, using mock embeddings"
        )
        # Fallback: simple mock embedding for development
        return await _generate_mock_embedding(text)


async def generate_embeddings_batch(
    texts: List[str],
    batch_size: int = 32
) -> List[List[float]]:
    """
    Generate embeddings for multiple texts in batches.
    
    Args:
        texts: List of texts to embed
        batch_size: Number of texts to process per batch
        
    Returns:
        List of embedding vectors
    """
    embeddings = []
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = await asyncio.gather(
            *[generate_embedding(text) for text in batch]
        )
        embeddings.extend(batch_embeddings)
        
        logger.info(
            f"Generated embeddings for batch {i//batch_size + 1}",
            extra={
                "batch_size": len(batch),
                "total": len(texts),
                "progress": f"{min(i + batch_size, len(texts))}/{len(texts)}"
            }
        )
    
    return embeddings


async def _generate_mock_embedding(text: str) -> List[float]:
    """
    Generate mock embedding for development/testing.
    Uses simple hashing to create deterministic embeddings.
    """
    # Simple deterministic mock based on text hash
    import hashlib
    
    hash_obj = hashlib.sha256(text.encode())
    hash_bytes = hash_obj.digest()
    
    # Convert hash bytes to normalized floats
    embedding = []
    for i in range(0, EMBEDDING_DIMENSIONS):
        byte_idx = i % len(hash_bytes)
        # Normalize to [-1, 1] range
        value = (hash_bytes[byte_idx] / 255.0) * 2 - 1
        embedding.append(value)
    
    logger.debug(
        f"Generated mock embedding (length: {len(text)})",
        extra={"dimensions": len(embedding)}
    )
    
    return embedding


async def cosine_similarity(
    embedding1: List[float],
    embedding2: List[float]
) -> float:
    """
    Calculate cosine similarity between two embeddings.
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
        
    Returns:
        Similarity score between -1 and 1 (1 = identical)
    """
    if len(embedding1) != len(embedding2):
        raise ValueError(
            f"Embedding dimensions don't match: "
            f"{len(embedding1)} vs {len(embedding2)}"
        )
    
    # Calculate dot product and magnitudes
    dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
    magnitude1 = sum(a * a for a in embedding1) ** 0.5
    magnitude2 = sum(b * b for b in embedding2) ** 0.5
    
    # Avoid division by zero
    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)


def get_embedding_info() -> dict:
    """Get information about current embedding configuration."""
    return {
        "model": EMBEDDING_MODEL,
        "dimensions": EMBEDDING_DIMENSIONS,
        "max_retries": MAX_RETRIES,
        "base_delay": BASE_DELAY,
        "max_delay": MAX_DELAY,
    }

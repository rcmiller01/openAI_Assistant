"""Unit tests for embedding generation."""

import pytest
from app.tools.embedding import (
    generate_embedding,
    generate_embeddings_batch,
    cosine_similarity,
    get_embedding_info,
    EMBEDDING_DIMENSIONS,
)


@pytest.mark.asyncio
async def test_generate_embedding():
    """Test basic embedding generation."""
    embedding = await generate_embedding("Hello world")
    
    assert isinstance(embedding, list)
    assert len(embedding) == EMBEDDING_DIMENSIONS
    assert all(isinstance(x, float) for x in embedding)


@pytest.mark.asyncio
async def test_generate_embedding_deterministic():
    """Test embeddings are deterministic (for mock)."""
    text = "Test text for embedding"
    
    emb1 = await generate_embedding(text)
    emb2 = await generate_embedding(text)
    
    assert emb1 == emb2


@pytest.mark.asyncio
async def test_generate_embeddings_batch():
    """Test batch embedding generation."""
    texts = ["First text", "Second text", "Third text"]
    
    embeddings = await generate_embeddings_batch(texts, batch_size=2)
    
    assert len(embeddings) == 3
    assert all(len(emb) == EMBEDDING_DIMENSIONS for emb in embeddings)


@pytest.mark.asyncio
async def test_cosine_similarity():
    """Test cosine similarity calculation."""
    emb1 = await generate_embedding("Hello world")
    emb2 = await generate_embedding("Hello world")
    emb3 = await generate_embedding("Completely different text")
    
    # Same text should have similarity close to 1
    sim_same = await cosine_similarity(emb1, emb2)
    assert sim_same == pytest.approx(1.0, abs=0.01)
    
    # Different text should have lower similarity
    sim_diff = await cosine_similarity(emb1, emb3)
    assert sim_diff < sim_same


@pytest.mark.asyncio
async def test_cosine_similarity_dimension_mismatch():
    """Test error on dimension mismatch."""
    emb1 = [1.0, 2.0, 3.0]
    emb2 = [1.0, 2.0]
    
    with pytest.raises(ValueError, match="don't match"):
        await cosine_similarity(emb1, emb2)


def test_get_embedding_info():
    """Test embedding configuration info."""
    info = get_embedding_info()
    
    assert "model" in info
    assert "dimensions" in info
    assert "max_retries" in info
    assert info["dimensions"] == EMBEDDING_DIMENSIONS

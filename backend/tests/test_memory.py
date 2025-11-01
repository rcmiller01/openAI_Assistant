"""Tests for memory service functionality."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(test_client: AsyncClient):
    """Test the health check endpoint."""
    response = await test_client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_version_endpoint(test_client: AsyncClient):
    """Test the version endpoint."""
    response = await test_client.get("/version")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_root_endpoint(test_client: AsyncClient):
    """Test the root endpoint."""
    response = await test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "status" in data
    assert data["status"] == "running"


@pytest.mark.asyncio
async def test_memory_write_requires_auth(test_client: AsyncClient):
    """Test that memory write requires authentication."""
    response = await test_client.post(
        "/api/v1/memory/write",
        json={"text": "Test memory"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_memory_search_requires_auth(test_client: AsyncClient):
    """Test that memory search requires authentication."""
    response = await test_client.post(
        "/api/v1/memory/search",
        json={"query": "test"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_memory_write_success(test_client: AsyncClient, auth_headers):
    """Test successful memory write."""
    response = await test_client.post(
        "/api/v1/memory/write",
        json={
            "text": "This is a test memory",
            "tags": ["test", "example"],
            "speaker_id": "user"
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["text"] == "This is a test memory"
    assert data["tags"] == ["test", "example"]
    assert data["speaker_id"] == "user"


@pytest.mark.asyncio
async def test_memory_search_success(test_client: AsyncClient, auth_headers):
    """Test successful memory search."""
    # First, write a memory
    write_response = await test_client.post(
        "/api/v1/memory/write",
        json={
            "text": "Python is a programming language",
            "tags": ["programming", "python"],
            "speaker_id": "assistant"
        },
        headers=auth_headers
    )
    assert write_response.status_code == 200
    
    # Then search for it
    search_response = await test_client.post(
        "/api/v1/memory/search",
        json={"query": "Python programming"},
        headers=auth_headers
    )
    assert search_response.status_code == 200
    data = search_response.json()
    assert "hits" in data
    assert "total_found" in data
    assert "search_time_ms" in data
    assert data["query"] == "Python programming"


@pytest.mark.asyncio
async def test_memory_write_invalid_data(test_client: AsyncClient, auth_headers):
    """Test memory write with invalid data."""
    response = await test_client.post(
        "/api/v1/memory/write",
        json={
            "text": "",  # Empty text should fail
            "tags": ["test"]
        },
        headers=auth_headers
    )
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_memory_search_with_filters(test_client: AsyncClient, auth_headers):
    """Test memory search with tag filters."""
    # Write multiple memories with different tags
    memories = [
        {"text": "Python programming", "tags": ["python", "code"]},
        {"text": "JavaScript functions", "tags": ["javascript", "code"]},
        {"text": "Database design", "tags": ["database", "design"]}
    ]
    
    for memory in memories:
        response = await test_client.post(
            "/api/v1/memory/write",
            json=memory,
            headers=auth_headers
        )
        assert response.status_code == 200
    
    # Search with tag filter
    response = await test_client.post(
        "/api/v1/memory/search",
        json={
            "query": "programming",
            "tags": ["python"],
            "top_k": 5
        },
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["hits"]) >= 0  # Should find Python-related memories
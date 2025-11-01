"""Unit tests for rate limiting."""

import pytest
import time
from app.core.rate_limit import (
    check_rate_limit,
    get_rate_limit_status,
    _rate_limit_store,
)


@pytest.fixture(autouse=True)
def clear_rate_limits():
    """Clear rate limit store before each test."""
    _rate_limit_store.clear()
    yield
    _rate_limit_store.clear()


@pytest.mark.asyncio
async def test_check_rate_limit_allow():
    """Test rate limit allows requests under limit."""
    key = "test_user_1"
    
    result = await check_rate_limit(key, limit=5, window_seconds=60)
    
    assert result["allowed"] is True
    assert result["remaining"] == 4
    assert result["limit"] == 5


@pytest.mark.asyncio
async def test_check_rate_limit_multiple_requests():
    """Test multiple requests decrement remaining."""
    key = "test_user_2"
    limit = 3
    
    # First request
    r1 = await check_rate_limit(key, limit=limit, window_seconds=60)
    assert r1["remaining"] == 2
    
    # Second request
    r2 = await check_rate_limit(key, limit=limit, window_seconds=60)
    assert r2["remaining"] == 1
    
    # Third request
    r3 = await check_rate_limit(key, limit=limit, window_seconds=60)
    assert r3["remaining"] == 0


@pytest.mark.asyncio
async def test_check_rate_limit_exceed():
    """Test rate limit blocks when exceeded."""
    key = "test_user_3"
    limit = 2
    
    # Use up limit
    await check_rate_limit(key, limit=limit, window_seconds=60)
    await check_rate_limit(key, limit=limit, window_seconds=60)
    
    # Next should be blocked
    result = await check_rate_limit(key, limit=limit, window_seconds=60)
    
    assert result["allowed"] is False
    assert result["remaining"] == 0


@pytest.mark.asyncio
async def test_check_rate_limit_reset():
    """Test rate limit resets after window."""
    key = "test_user_4"
    limit = 2
    window = 1  # 1 second window
    
    # Use up limit
    await check_rate_limit(key, limit=limit, window_seconds=window)
    await check_rate_limit(key, limit=limit, window_seconds=window)
    
    # Should be blocked
    r1 = await check_rate_limit(key, limit=limit, window_seconds=window)
    assert r1["allowed"] is False
    
    # Wait for window to expire
    time.sleep(window + 0.1)
    
    # Should be allowed again
    r2 = await check_rate_limit(key, limit=limit, window_seconds=window)
    assert r2["allowed"] is True
    assert r2["remaining"] == limit - 1


@pytest.mark.asyncio
async def test_get_rate_limit_status():
    """Test getting rate limit status."""
    key = "test_user_5"
    
    # Make some requests
    await check_rate_limit(key, limit=10, window_seconds=60)
    await check_rate_limit(key, limit=10, window_seconds=60)
    
    # Check status
    status = await get_rate_limit_status(key)
    
    assert "remaining" in status
    assert "limit" in status
    assert "count" in status or "remaining" in status

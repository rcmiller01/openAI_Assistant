"""Rate limiting with Redis token bucket implementation."""

import os
import time
import logging
from typing import Dict, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

# Configuration
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "false").lower() == "true"
DEFAULT_RATE_LIMIT = int(os.getenv("DEFAULT_RATE_LIMIT", "60"))
DEFAULT_WINDOW_SECONDS = int(os.getenv("DEFAULT_WINDOW_SECONDS", "60"))

# In-memory rate limit store (fallback when Redis unavailable)
_rate_limit_store: Dict[str, Dict[str, Any]] = defaultdict(
    lambda: {"count": 0, "reset_time": 0}
)

# Redis client (initialized on first use)
_redis_client: Optional[Any] = None


def _get_redis_client():
    """Get or create Redis client."""
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    try:
        import redis.asyncio as redis
        
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _redis_client = redis.from_url(redis_url, decode_responses=True)
        
        logger.info(f"Connected to Redis for rate limiting: {redis_url}")
        return _redis_client
        
    except ImportError:
        logger.warning(
            "Redis not available. Using in-memory rate limiting. "
            "Install with: pip install redis"
        )
        return None


async def check_rate_limit(
    key: str,
    limit: int = DEFAULT_RATE_LIMIT,
    window_seconds: int = DEFAULT_WINDOW_SECONDS
) -> Dict[str, Any]:
    """
    Check rate limit using token bucket algorithm.
    
    Args:
        key: Rate limit key (e.g., user_id, ip_address, intent)
        limit: Max requests per window
        window_seconds: Time window in seconds
        
    Returns:
        Dict with allowed (bool), remaining (int), reset_time (int)
        
    Raises:
        Exception: If rate limit exceeded
    """
    if not RATE_LIMIT_ENABLED:
        return {
            "allowed": True,
            "remaining": limit,
            "reset_time": int(time.time() + window_seconds),
            "limit": limit,
        }
    
    redis = _get_redis_client()
    
    if redis:
        return await _check_rate_limit_redis(
            redis, key, limit, window_seconds
        )
    else:
        return await _check_rate_limit_memory(key, limit, window_seconds)


async def _check_rate_limit_redis(
    redis,
    key: str,
    limit: int,
    window_seconds: int
) -> Dict[str, Any]:
    """Token bucket implementation with Redis."""
    now = int(time.time())
    redis_key = f"ratelimit:{key}"
    
    try:
        # Get current count and reset time
        pipeline = redis.pipeline()
        pipeline.get(f"{redis_key}:count")
        pipeline.get(f"{redis_key}:reset")
        results = await pipeline.execute()
        
        count = int(results[0]) if results[0] else 0
        reset_time = int(results[1]) if results[1] else now + window_seconds
        
        # Reset if window expired
        if now >= reset_time:
            count = 0
            reset_time = now + window_seconds
        
        # Check limit
        if count >= limit:
            logger.warning(
                f"Rate limit exceeded for key: {key[:8]}...",
                extra={"key": key, "count": count, "limit": limit}
            )
            return {
                "allowed": False,
                "remaining": 0,
                "reset_time": reset_time,
                "limit": limit,
            }
        
        # Increment count
        count += 1
        pipeline = redis.pipeline()
        pipeline.set(f"{redis_key}:count", count, ex=window_seconds)
        pipeline.set(f"{redis_key}:reset", reset_time, ex=window_seconds)
        await pipeline.execute()
        
        return {
            "allowed": True,
            "remaining": limit - count,
            "reset_time": reset_time,
            "limit": limit,
        }
        
    except Exception as e:
        logger.error(f"Redis rate limit check failed: {e}")
        # Fallback to memory-based
        return await _check_rate_limit_memory(key, limit, window_seconds)


async def _check_rate_limit_memory(
    key: str,
    limit: int,
    window_seconds: int
) -> Dict[str, Any]:
    """In-memory token bucket (fallback)."""
    now = int(time.time())
    bucket = _rate_limit_store[key]
    
    # Reset if window expired
    if now >= bucket["reset_time"]:
        bucket["count"] = 0
        bucket["reset_time"] = now + window_seconds
    
    # Check limit
    if bucket["count"] >= limit:
        logger.warning(
            f"Rate limit exceeded (memory) for key: {key[:8]}...",
            extra={"key": key, "count": bucket["count"], "limit": limit}
        )
        return {
            "allowed": False,
            "remaining": 0,
            "reset_time": bucket["reset_time"],
            "limit": limit,
        }
    
    # Increment
    bucket["count"] += 1
    
    return {
        "allowed": True,
        "remaining": limit - bucket["count"],
        "reset_time": bucket["reset_time"],
        "limit": limit,
    }


async def get_rate_limit_status(key: str) -> Dict[str, Any]:
    """
    Get current rate limit status without incrementing.
    
    Args:
        key: Rate limit key
        
    Returns:
        Dict with current status
    """
    if not RATE_LIMIT_ENABLED:
        return {
            "enabled": False,
            "remaining": DEFAULT_RATE_LIMIT,
            "limit": DEFAULT_RATE_LIMIT,
        }
    
    redis = _get_redis_client()
    
    if redis:
        try:
            redis_key = f"ratelimit:{key}"
            count = await redis.get(f"{redis_key}:count")
            count = int(count) if count else 0
            
            return {
                "enabled": True,
                "remaining": max(0, DEFAULT_RATE_LIMIT - count),
                "limit": DEFAULT_RATE_LIMIT,
                "count": count,
            }
        except Exception as e:
            logger.error(f"Failed to get rate limit status: {e}")
    
    # Memory fallback
    bucket = _rate_limit_store.get(key, {"count": 0})
    return {
        "enabled": True,
        "remaining": max(0, DEFAULT_RATE_LIMIT - bucket["count"]),
        "limit": DEFAULT_RATE_LIMIT,
        "count": bucket["count"],
    }


async def check_quota(key: str) -> None:
    """
    Legacy function - check rate limit and raise if exceeded.
    
    Args:
        key: The rate limit key
        
    Raises:
        Exception: If rate limit exceeded
    """
    result = await check_rate_limit(key)
    
    if not result["allowed"]:
        raise Exception(
            f"Rate limit exceeded. "
            f"Retry after {result['reset_time'] - int(time.time())}s"
        )


def get_quota_status(key: str) -> Dict[str, Any]:
    """
    Legacy sync function for quota status.
    
    Args:
        key: The rate limit key
        
    Returns:
        Dict containing quota information
    """
    bucket = _rate_limit_store.get(key, {"count": 0, "reset_time": 0})
    
    return {
        "key": key[:8] + "...",
        "requests_remaining": max(0, DEFAULT_RATE_LIMIT - bucket["count"]),
        "reset_time": bucket["reset_time"],
        "rate_limit_enabled": RATE_LIMIT_ENABLED,
    }
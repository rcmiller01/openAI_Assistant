"""Authentication dependencies and utilities."""

import os
import logging
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.rate_limit import check_quota

logger = logging.getLogger(__name__)

# Initialize HTTP Bearer security scheme
security = HTTPBearer()

# Get API key from environment
API_KEY = os.getenv("API_KEY", "replace-me-with-a-long-random-string")

if API_KEY == "replace-me-with-a-long-random-string":
    logger.warning("Using default API key - change this in production!")


async def api_auth(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> str:
    """
    Validate API key from Authorization header.
    
    Args:
        credentials: HTTP Authorization credentials from Bearer token
        
    Returns:
        str: The validated token
        
    Raises:
        HTTPException: 401 if token is missing or invalid
    """
    if not credentials:
        logger.warning("Authentication attempt with no credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    if not token:
        logger.warning("Authentication attempt with empty token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if token != API_KEY:
        logger.warning(f"Authentication failed for token: {token[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Apply rate limiting
    try:
        await check_quota(token)
    except Exception as e:
        logger.warning(f"Rate limit check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )
    
    logger.debug("Authentication successful")
    return token


# Type alias for dependency injection
AuthenticatedUser = Annotated[str, Depends(api_auth)]
"""HTTP fetch router with security controls."""

import os
import logging
import socket
import ipaddress
from urllib.parse import urlparse
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, status, Query, Depends
from pydantic import BaseModel

from app.deps.auth import AuthenticatedUser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/fetch", tags=["fetch"])

# Get domain allowlist from environment
FETCH_DOMAIN_ALLOWLIST = os.getenv("FETCH_DOMAIN_ALLOWLIST", "").split(",")
FETCH_DOMAIN_ALLOWLIST = [d.strip() for d in FETCH_DOMAIN_ALLOWLIST if d.strip()]

# Private IP ranges to block
PRIVATE_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


class FetchOut(BaseModel):
    """HTTP fetch response."""
    url: str
    status_code: int
    content_type: Optional[str] = None
    size: int
    text: str
    truncated: bool


def is_private_ip(ip_str: str) -> bool:
    """Check if IP address is private/internal."""
    try:
        ip = ipaddress.ip_address(ip_str)
        for network in PRIVATE_IP_RANGES:
            if ip in network:
                return True
        return False
    except ValueError:
        return False


def validate_url(url: str) -> tuple[str, str]:
    """
    Validate URL for security.
    
    Args:
        url: URL to validate
        
    Returns:
        tuple: (scheme, hostname)
        
    Raises:
        HTTPException: If URL is invalid or unsafe
    """
    parsed = urlparse(url)
    
    # Enforce HTTPS only
    if parsed.scheme != "https":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only HTTPS URLs are allowed"
        )
    
    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL: no hostname"
        )
    
    # Check domain allowlist
    allowed = False
    for allowed_domain in FETCH_DOMAIN_ALLOWLIST:
        if hostname == allowed_domain or hostname.endswith(f".{allowed_domain}"):
            allowed = True
            break
    
    if not allowed:
        logger.warning(f"Blocked request to non-allowlisted domain: {hostname}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Domain not in allowlist: {hostname}"
        )
    
    # Resolve DNS and check for private IPs
    try:
        addr_info = socket.getaddrinfo(hostname, None)
        for family, _, _, _, sockaddr in addr_info:
            ip = sockaddr[0]
            if is_private_ip(ip):
                logger.warning(f"Blocked request to private IP: {hostname} -> {ip}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Requests to private IP addresses are not allowed"
                )
    except socket.gaierror:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to resolve hostname"
        )
    
    return parsed.scheme, hostname


@router.get("/get", response_model=FetchOut)
async def fetch_url(
    _token: AuthenticatedUser,
    url: str = Query(..., description="HTTPS URL to fetch"),
    max_bytes: int = Query(262144, ge=1, le=10485760, description="Max bytes")
) -> FetchOut:
    """
    Fetch content from a URL with security controls.
    
    Only HTTPS URLs are allowed.
    Domain must be in the allowlist.
    Private/internal IPs are blocked.
    
    Args:
        url: HTTPS URL to fetch
        max_bytes: Maximum bytes to download
        
    Returns:
        FetchOut: Fetched content
    """
    try:
        # Validate URL
        validate_url(url)
        
        # Fetch content
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            max_redirects=3
        ) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"HTTP error: {e.response.status_code}"
                )
            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to fetch URL"
                )
            
            content_type = response.headers.get("content-type", "")
            content = response.text
            full_size = len(content)
            
            # Truncate if needed
            truncated = False
            if len(content) > max_bytes:
                content = content[:max_bytes]
                truncated = True
            
            return FetchOut(
                url=url,
                status_code=response.status_code,
                content_type=content_type,
                size=full_size,
                text=content,
                truncated=truncated
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch URL"
        )

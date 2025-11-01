"""HMAC signature verification for webhooks and callbacks."""

import os
import hmac
import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Configuration
HMAC_SECRET = os.getenv("HMAC_SECRET", "")
HMAC_HEADER = os.getenv("HMAC_HEADER", "X-Signature")
HMAC_ALGORITHM = os.getenv("HMAC_ALGORITHM", "sha256")


def generate_signature(payload: bytes, secret: Optional[str] = None) -> str:
    """
    Generate HMAC signature for payload.
    
    Args:
        payload: Raw bytes to sign
        secret: Optional secret (uses HMAC_SECRET if not provided)
        
    Returns:
        Hex-encoded signature
    """
    secret_key = (secret or HMAC_SECRET).encode()
    
    if HMAC_ALGORITHM == "sha256":
        signature = hmac.new(secret_key, payload, hashlib.sha256)
    elif HMAC_ALGORITHM == "sha512":
        signature = hmac.new(secret_key, payload, hashlib.sha512)
    else:
        signature = hmac.new(secret_key, payload, hashlib.sha256)
    
    return signature.hexdigest()


def verify_signature(
    payload: bytes,
    signature: str,
    secret: Optional[str] = None
) -> bool:
    """
    Verify HMAC signature for payload.
    
    Args:
        payload: Raw bytes to verify
        signature: Hex-encoded signature to check
        secret: Optional secret (uses HMAC_SECRET if not provided)
        
    Returns:
        True if signature is valid
    """
    if not HMAC_SECRET and not secret:
        logger.warning(
            "HMAC_SECRET not configured - signature verification disabled"
        )
        return True  # Allow requests when HMAC not configured
    
    expected_signature = generate_signature(payload, secret)
    
    # Use constant-time comparison to prevent timing attacks
    is_valid = hmac.compare_digest(signature, expected_signature)
    
    if not is_valid:
        logger.warning(
            "HMAC signature verification failed",
            extra={
                "expected_prefix": expected_signature[:8],
                "received_prefix": signature[:8],
            }
        )
    
    return is_valid


def get_signature_header() -> str:
    """Get the header name used for HMAC signatures."""
    return HMAC_HEADER


def is_hmac_enabled() -> bool:
    """Check if HMAC verification is enabled."""
    return bool(HMAC_SECRET)

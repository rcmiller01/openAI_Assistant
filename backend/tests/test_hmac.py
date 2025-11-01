"""Unit tests for HMAC signature verification."""

import pytest
from app.core.hmac import (
    generate_signature,
    verify_signature,
    get_signature_header,
    is_hmac_enabled,
)


def test_generate_signature():
    """Test signature generation."""
    payload = b"test payload"
    secret = "test_secret"
    
    signature = generate_signature(payload, secret)
    
    assert isinstance(signature, str)
    assert len(signature) == 64  # SHA256 hex = 64 chars


def test_generate_signature_deterministic():
    """Test signatures are deterministic."""
    payload = b"test payload"
    secret = "test_secret"
    
    sig1 = generate_signature(payload, secret)
    sig2 = generate_signature(payload, secret)
    
    assert sig1 == sig2


def test_verify_signature_valid():
    """Test valid signature verification."""
    payload = b"test payload"
    secret = "test_secret"
    
    signature = generate_signature(payload, secret)
    is_valid = verify_signature(payload, signature, secret)
    
    assert is_valid is True


def test_verify_signature_invalid():
    """Test invalid signature detection."""
    payload = b"test payload"
    secret = "test_secret"
    wrong_signature = "0" * 64
    
    is_valid = verify_signature(payload, wrong_signature, secret)
    
    assert is_valid is False


def test_verify_signature_tampered_payload():
    """Test tampered payload detection."""
    payload = b"test payload"
    tampered_payload = b"test payload modified"
    secret = "test_secret"
    
    signature = generate_signature(payload, secret)
    is_valid = verify_signature(tampered_payload, signature, secret)
    
    assert is_valid is False


def test_get_signature_header():
    """Test getting signature header name."""
    header = get_signature_header()
    assert isinstance(header, str)
    assert len(header) > 0


def test_is_hmac_enabled():
    """Test HMAC enabled check."""
    # Returns bool based on HMAC_SECRET env var
    enabled = is_hmac_enabled()
    assert isinstance(enabled, bool)

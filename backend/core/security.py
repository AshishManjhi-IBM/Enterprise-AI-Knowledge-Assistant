"""
Security helpers — Phase 10 Production Readiness.

Provides:
  - JWT access-token creation and verification
  - API-key hashing and comparison
  - Password hashing helpers

All secrets are read from ``settings``.  Never hard-code keys here.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from backend.core.settings import settings
from backend.core.logging import get_logger

logger = get_logger(__name__)

# ── Optional dependency guard ─────────────────────────────────────────────

try:
    import jwt as _jwt          # PyJWT
    _JWT_AVAILABLE = True
except ImportError:             # pragma: no cover
    _JWT_AVAILABLE = False


# ── JWT helpers ───────────────────────────────────────────────────────────

def create_access_token(
    subject: str,
    extra_claims: Optional[Dict[str, Any]] = None,
    expire_minutes: Optional[int] = None,
) -> str:
    """
    Create a signed JWT access token.

    Parameters
    ----------
    subject:
        The ``sub`` claim — typically a username or user ID.
    extra_claims:
        Additional key-value pairs to embed in the payload.
    expire_minutes:
        Override the default expiry from settings.

    Returns
    -------
    str
        Encoded JWT string.

    Raises
    ------
    RuntimeError
        If PyJWT is not installed.
    """
    if not _JWT_AVAILABLE:
        raise RuntimeError(
            "PyJWT is not installed. Run: pip install PyJWT>=2.8"
        )

    expire = datetime.now(tz=timezone.utc) + timedelta(
        minutes=expire_minutes or settings.jwt_expire_minutes
    )
    payload: Dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(tz=timezone.utc),
    }
    if extra_claims:
        payload.update(extra_claims)

    return _jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT access token.

    Parameters
    ----------
    token:
        Encoded JWT string.

    Returns
    -------
    dict
        Decoded payload.

    Raises
    ------
    jwt.ExpiredSignatureError
        If the token has expired.
    jwt.InvalidTokenError
        If the token is invalid or tampered with.
    RuntimeError
        If PyJWT is not installed.
    """
    if not _JWT_AVAILABLE:
        raise RuntimeError(
            "PyJWT is not installed. Run: pip install PyJWT>=2.8"
        )

    return _jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


# ── API-key helpers ───────────────────────────────────────────────────────

def generate_api_key(prefix: str = "sk") -> str:
    """Generate a random URL-safe API key in the form ``{prefix}-{token}``."""
    return f"{prefix}-{secrets.token_urlsafe(32)}"


def hash_api_key(raw_key: str) -> str:
    """Return a SHA-256 hex digest of the API key for safe storage."""
    return hashlib.sha256(raw_key.encode()).hexdigest()


def verify_api_key(raw_key: str, stored_hash: str) -> bool:
    """Constant-time comparison of ``hash_api_key(raw_key)`` vs ``stored_hash``."""
    return hmac.compare_digest(
        hash_api_key(raw_key).encode(),
        stored_hash.encode(),
    )


# Made with Bob

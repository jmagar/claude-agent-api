"""Cryptographic utilities for secure API key handling.

This module provides functions for securely hashing and verifying API keys
using SHA-256 with constant-time comparison to prevent timing attacks.

Security Features:
- SHA-256 hashing (cryptographically secure)
- Constant-time comparison (prevents timing attacks)
- No plaintext storage (OWASP security best practice)

Note:
    SHA-256 is acceptable for API key hashing because:
    - API keys are high-entropy (random UUIDs or similar)
    - No password-specific attacks (dictionary, rainbow tables) apply
    - No need for slow key derivation (bcrypt/scrypt) overhead
    - Constant-time comparison prevents timing side-channels
"""

import hashlib
import secrets

API_KEY_HASH_ALGORITHM = "sha256"


def hash_api_key(api_key: str) -> str:
    """Hash API key using SHA-256.

    Args:
        api_key: Plaintext API key to hash.

    Returns:
        Hexadecimal hash digest (64 characters).

    Security:
        Uses SHA-256 for cryptographic hashing. Algorithm can be changed
        via API_KEY_HASH_ALGORITHM constant for future migrations.

    Example:
        >>> hash_api_key("test-key-12345")
        '953a6f3acb148f7d0492a99ed5ce98dd442326f6438b39625fd5c85efa7f6f21'
    """
    return hashlib.new(API_KEY_HASH_ALGORITHM, api_key.encode()).hexdigest()


def verify_api_key(api_key: str, hashed: str) -> bool:
    """Verify API key against hash in constant time.

    Uses constant-time comparison to prevent timing attacks where
    attackers can infer hash contents by measuring response times.

    Args:
        api_key: Plaintext API key to verify.
        hashed: Stored hash to compare against.

    Returns:
        True if API key matches hash, False otherwise.

    Example:
        >>> hashed = hash_api_key("test-key-12345")
        >>> verify_api_key("test-key-12345", hashed)
        True
        >>> verify_api_key("wrong-key", hashed)
        False
    """
    return secrets.compare_digest(hash_api_key(api_key), hashed)

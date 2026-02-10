"""Tests for cryptographic utilities."""

import hashlib

import pytest

from apps.api.utils.crypto import hash_api_key, verify_api_key


class TestHashApiKey:
    """Tests for hash_api_key function."""

    def test_hash_api_key_returns_sha256_hex(self) -> None:
        """hash_api_key should return SHA-256 hex digest."""
        api_key = "test-key-12345"
        expected = hashlib.sha256(api_key.encode()).hexdigest()

        result = hash_api_key(api_key)

        assert result == expected
        assert len(result) == 64  # SHA-256 produces 64 hex characters
        assert all(c in "0123456789abcdef" for c in result)

    def test_hash_api_key_different_keys_produce_different_hashes(self) -> None:
        """Different API keys should produce different hashes."""
        key1 = "test-key-1"
        key2 = "test-key-2"

        hash1 = hash_api_key(key1)
        hash2 = hash_api_key(key2)

        assert hash1 != hash2

    def test_hash_api_key_same_key_produces_same_hash(self) -> None:
        """Same API key should always produce same hash (deterministic)."""
        api_key = "test-key-12345"

        hash1 = hash_api_key(api_key)
        hash2 = hash_api_key(api_key)
        hash3 = hash_api_key(api_key)

        assert hash1 == hash2 == hash3

    def test_hash_api_key_handles_empty_string(self) -> None:
        """hash_api_key should handle empty string."""
        result = hash_api_key("")

        assert len(result) == 64
        assert result == hashlib.sha256(b"").hexdigest()

    def test_hash_api_key_handles_special_characters(self) -> None:
        """hash_api_key should handle special characters."""
        api_key = "test!@#$%^&*()_+-={}[]|\\:;\"'<>,.?/"

        result = hash_api_key(api_key)

        assert len(result) == 64
        assert result == hashlib.sha256(api_key.encode()).hexdigest()

    def test_hash_api_key_handles_unicode(self) -> None:
        """hash_api_key should handle Unicode characters."""
        api_key = "test-key-🔑-unicode"

        result = hash_api_key(api_key)

        assert len(result) == 64
        assert result == hashlib.sha256(api_key.encode()).hexdigest()


class TestVerifyApiKey:
    """Tests for verify_api_key function."""

    def test_verify_api_key_returns_true_for_matching_key(self) -> None:
        """verify_api_key should return True for matching key."""
        api_key = "test-key-12345"
        hashed = hash_api_key(api_key)

        result = verify_api_key(api_key, hashed)

        assert result is True

    def test_verify_api_key_returns_false_for_non_matching_key(self) -> None:
        """verify_api_key should return False for non-matching key."""
        correct_key = "test-key-12345"
        wrong_key = "test-key-67890"
        hashed = hash_api_key(correct_key)

        result = verify_api_key(wrong_key, hashed)

        assert result is False

    def test_verify_api_key_returns_false_for_empty_key(self) -> None:
        """verify_api_key should return False when verifying empty key against hash."""
        api_key = "test-key-12345"
        hashed = hash_api_key(api_key)

        result = verify_api_key("", hashed)

        assert result is False

    def test_verify_api_key_returns_false_for_case_mismatch(self) -> None:
        """verify_api_key should be case-sensitive."""
        api_key = "test-key-12345"
        hashed = hash_api_key(api_key)

        result = verify_api_key("TEST-KEY-12345", hashed)

        assert result is False

    def test_verify_api_key_returns_false_for_similar_key(self) -> None:
        """verify_api_key should reject even slightly different keys."""
        api_key = "test-key-12345"
        hashed = hash_api_key(api_key)

        # Test various similar but different keys
        assert verify_api_key("test-key-12345 ", hashed) is False  # trailing space
        assert verify_api_key(" test-key-12345", hashed) is False  # leading space
        assert verify_api_key("test-key-123456", hashed) is False  # extra char
        assert verify_api_key("test-key-1234", hashed) is False  # missing char

    @pytest.mark.timing
    @pytest.mark.slow
    def test_verify_api_key_uses_constant_time_comparison(self) -> None:
        """verify_api_key should use constant-time comparison.

        This test verifies that we're using secrets.compare_digest()
        by checking that the function doesn't leak timing information
        through early returns.

        NOTE: This is a timing-sensitive test that may be flaky in CI
        environments with high load or virtualization overhead. Use
        @pytest.mark.timing or @pytest.mark.slow to exclude from default runs.
        """
        import time

        api_key = "test-key-12345"
        hashed = hash_api_key(api_key)

        # Compare timing for correct vs incorrect keys
        # In a non-constant-time implementation, the first character
        # mismatch would cause an early return (faster).
        # With constant-time comparison, both should take similar time.

        # Correct key (all characters match)
        iterations = 1000
        start = time.perf_counter()
        for _ in range(iterations):
            verify_api_key(api_key, hashed)
        correct_time = time.perf_counter() - start

        # Completely wrong key (first character different)
        wrong_key = "WRONG-key-12345"
        start = time.perf_counter()
        for _ in range(iterations):
            verify_api_key(wrong_key, hashed)
        wrong_time = time.perf_counter() - start

        # Timing should be similar (within 100% variance due to system noise)
        # In a vulnerable implementation, wrong_time would be significantly faster
        # Note: This test is probabilistic and may have false positives on busy systems
        time_ratio = max(correct_time, wrong_time) / min(correct_time, wrong_time)
        assert time_ratio < 2.0, (
            f"Timing difference suggests non-constant-time comparison: "
            f"correct={correct_time:.6f}s, wrong={wrong_time:.6f}s, "
            f"ratio={time_ratio:.2f}"
        )

    def test_verify_api_key_handles_invalid_hash_format(self) -> None:
        """verify_api_key should handle invalid hash formats gracefully."""
        api_key = "test-key-12345"

        # Invalid hash (too short)
        assert verify_api_key(api_key, "invalid") is False

        # Invalid hash (wrong length)
        assert verify_api_key(api_key, "a" * 63) is False
        assert verify_api_key(api_key, "a" * 65) is False

        # Invalid hash (non-hex characters)
        assert verify_api_key(api_key, "g" * 64) is False


class TestSecurityProperties:
    """Tests for security properties of the crypto module."""

    def test_hash_collision_resistance(self) -> None:
        """Different keys should produce different hashes (collision resistance)."""
        keys = [
            "test-key-1",
            "test-key-2",
            "test-key-3",
            "another-key",
            "completely-different-key",
        ]

        hashes = [hash_api_key(key) for key in keys]

        # All hashes should be unique
        assert len(hashes) == len(set(hashes))

    def test_hash_avalanche_effect(self) -> None:
        """Small change in input should produce large change in output."""
        key1 = "test-key-12345"
        key2 = "test-key-12346"  # Only last character different

        hash1 = hash_api_key(key1)
        hash2 = hash_api_key(key2)

        # Count differing bits
        diff_bits = sum(
            bin(int(c1, 16) ^ int(c2, 16)).count("1")
            for c1, c2 in zip(hash1, hash2, strict=True)
        )

        # SHA-256 avalanche effect: ~50% of bits should differ for 1-char change
        # For 256-bit hash (64 hex chars, 4 bits each), expect ~128 bits different
        # Allow range of 100-156 bits (39-61% of 256 bits) to account for variance
        assert 100 <= diff_bits <= 156, (
            f"Avalanche effect too weak: only {diff_bits}/256 bits differ "
            f"({diff_bits / 256 * 100:.1f}%)"
        )

    def test_irreversibility(self) -> None:
        """Hash should be one-way (cannot recover key from hash)."""
        api_key = "test-key-12345"
        hashed = hash_api_key(api_key)

        # Hash should not contain the original key
        assert api_key not in hashed
        assert api_key.encode() not in hashed.encode()

        # Hash should be hexadecimal (no direct encoding of original)
        assert all(c in "0123456789abcdef" for c in hashed)

    @pytest.mark.parametrize(
        "api_key",
        [
            "simple-key",
            "key-with-numbers-123456",
            "key!@#$%^&*()special",
            "very-long-key-" + "x" * 100,
            "unicode-🔑-key",
            "",  # edge case: empty string
        ],
    )
    def test_hash_determinism_across_inputs(self, api_key: str) -> None:
        """All input types should hash deterministically."""
        hash1 = hash_api_key(api_key)
        hash2 = hash_api_key(api_key)

        assert hash1 == hash2
        assert len(hash1) == 64

"""Integration tests for hash consistency verification script.

Tests the verify_hash_consistency.py script to ensure it correctly exits
with appropriate codes and provides meaningful output.

NOTE: These tests verify the script's basic functionality (exit codes, output format).
The script itself has comprehensive logic to detect hash mismatches and uses database
queries directly. Full end-to-end testing with real mismatches requires database setup
and is better done manually or in staging environments.
"""

import subprocess


def test_script_exits_with_status_code() -> None:
    """Test script exits with appropriate status code (0 or 1).

    NOTE: This test may find real hash mismatches in test database if Phase 1
    migration hasn't been run. That's expected behavior - the script is working
    correctly. Exit code 0 = all match, exit code 1 = mismatches found.
    """
    import sys

    result = subprocess.run(
        [sys.executable, "scripts/verify_hash_consistency.py"],
        capture_output=True,
        text=True,
    )

    # Script should exit with 0 (success) or 1 (found mismatches)
    assert result.returncode in (0, 1), (
        f"Script exited with unexpected code {result.returncode}: {result.stderr}"
    )
    assert "VERIFICATION" in result.stdout
    assert "Total records checked:" in result.stdout
    assert "Records with matching hashes:" in result.stdout
    assert "Records with mismatches:" in result.stdout


def test_script_shows_summary_statistics() -> None:
    """Test script provides comprehensive summary output."""
    import sys

    result = subprocess.run(
        [sys.executable, "scripts/verify_hash_consistency.py"],
        capture_output=True,
        text=True,
    )

    # Verify script provides all expected sections
    assert "[1/2] Verifying sessions table..." in result.stdout
    assert "[2/2] Verifying assistants table..." in result.stdout
    assert "SUMMARY" in result.stdout
    assert "Total records checked:" in result.stdout


def test_script_requires_database_url() -> None:
    """Test script fails gracefully when DATABASE_URL is not set."""
    import sys

    # Run script without DATABASE_URL environment variable
    result = subprocess.run(
        [sys.executable, "scripts/verify_hash_consistency.py"],
        capture_output=True,
        text=True,
        env={},  # Empty environment (no DATABASE_URL)
    )

    # Script should exit with code 1 when DATABASE_URL is missing
    assert result.returncode == 1
    assert "DATABASE_URL environment variable not set" in result.stderr
    assert "USAGE:" in result.stderr


def test_script_has_correct_docstring() -> None:
    """Test script has comprehensive docstring with usage instructions."""
    with open("scripts/verify_hash_consistency.py") as f:
        content = f.read()

    # Verify script has proper documentation
    assert '"""Hash Consistency Verification Script.' in content
    assert "WHY THIS MATTERS:" in content
    assert "WHEN TO RUN:" in content
    assert "WHAT IT CHECKS:" in content
    assert "EXIT CODES:" in content
    assert "USAGE:" in content


def test_script_is_executable() -> None:
    """Test script has executable permissions."""
    import os
    import stat

    script_path = "scripts/verify_hash_consistency.py"
    st = os.stat(script_path)
    is_executable = bool(st.st_mode & stat.S_IXUSR)

    assert is_executable, f"{script_path} should have executable permissions"


def test_script_uses_correct_hash_function() -> None:
    """Test script uses SHA-256 hash function matching the application."""
    with open("scripts/verify_hash_consistency.py") as f:
        content = f.read()

    # Verify script uses SHA-256 (not MD5, SHA1, or other algorithms)
    assert "hashlib.sha256" in content
    assert "sha256" in content
    # Ensure it matches database computation
    assert "digest(owner_api_key, 'sha256')" in content

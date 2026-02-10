"""Integration tests for hash consistency verification script (Phase 3).

Tests the verify_hash_consistency.py script to ensure it correctly exits
with appropriate codes and provides meaningful output.

NOTE: After Phase 3, the script verifies that plaintext columns have been removed
and hash columns exist, rather than comparing plaintext to hash values.
"""

import subprocess
from pathlib import Path


def test_script_exits_with_status_code() -> None:
    """Test script exits with appropriate status code (0 or 1).

    After Phase 3, script verifies hash columns exist and reports migration status.
    """
    import sys

    result = subprocess.run(
        [sys.executable, "scripts/verify_hash_consistency.py"],
        capture_output=True,
        text=True,
    )

    # Script should exit with 0 (success) or 1 (error)
    assert result.returncode in (0, 1), (
        f"Script exited with unexpected code {result.returncode}: {result.stderr}"
    )
    # Phase 3 script outputs VERIFICATION or PHASE 3
    assert "VERIFICATION" in result.stdout or "PHASE 3" in result.stdout
    assert "owner_api_key_hash" in result.stdout


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
    content = Path("scripts/verify_hash_consistency.py").read_text()

    # Verify script has proper documentation
    assert '"""Hash Consistency Verification Script.' in content
    assert "PHASE 3" in content
    assert "EXIT CODES:" in content
    assert "USAGE:" in content


def test_script_is_executable() -> None:
    """Test script has executable permissions."""
    import stat

    script_path = Path("scripts/verify_hash_consistency.py")
    st = script_path.stat()
    is_executable = bool(st.st_mode & stat.S_IXUSR)

    assert is_executable, f"{script_path} should have executable permissions"


def test_script_checks_hash_column_existence() -> None:
    """Test script verifies hash columns exist after Phase 3."""
    content = Path("scripts/verify_hash_consistency.py").read_text()

    # Verify script checks for hash column existence
    assert "owner_api_key_hash" in content
    assert "check_column_exists" in content

#!/usr/bin/env python3
"""Hash Consistency Verification Script.

This script verifies that all owner_api_key_hash values in the sessions and
assistants tables correctly match the SHA-256 hash of their corresponding
owner_api_key plaintext values.

WHY THIS MATTERS:
During the phased migration to hashed API keys (Issues #1-#7), we temporarily
maintain both plaintext (owner_api_key) and hashed (owner_api_key_hash) columns.
This script detects data corruption or inconsistencies before Phase 3, which will
drop the plaintext column permanently.

WHEN TO RUN:
- After Phase 1 (migration adds hash column) - baseline verification
- After Phase 2 (app uses hashes) - verify no corruption during transition
- Before Phase 3 (drop plaintext column) - MANDATORY pre-deployment check
- Periodically during Phase 2 as a health check

WHAT IT CHECKS:
For each record with owner_api_key NOT NULL:
1. Computes SHA-256 hash of owner_api_key (plaintext)
2. Compares with owner_api_key_hash (stored hash)
3. Reports mismatches as data corruption

EXIT CODES:
0 - All hashes match (safe to proceed)
1 - Mismatches found (DO NOT DEPLOY PHASE 3)

USAGE:
    export DATABASE_URL="postgresql://user:pass@host:port/dbname"
    uv run python scripts/verify_hash_consistency.py

    # Or with inline DATABASE_URL:
    DATABASE_URL="postgresql://..." uv run python scripts/verify_hash_consistency.py
"""

import asyncio
import hashlib
import os
import sys
from collections.abc import Sequence
from typing import Protocol

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


class RecordWithApiKey(Protocol):
    """Protocol for database records with API key fields."""

    owner_api_key: str | None
    owner_api_key_hash: str | None


def hash_api_key(api_key: str) -> str:
    """Compute SHA-256 hash of API key (matches database computation).

    Args:
        api_key: Plaintext API key.

    Returns:
        Hexadecimal SHA-256 hash string (64 characters).
    """
    return hashlib.sha256(api_key.encode()).hexdigest()


async def verify_table_hashes(
    session: AsyncSession, table_name: str
) -> tuple[int, int, list[str]]:
    """Verify hash consistency for a single table.

    Args:
        session: Database session.
        table_name: Name of table to verify ('sessions' or 'assistants').

    Returns:
        Tuple of (total_checked, mismatches_count, mismatch_details).
    """
    # Use raw SQL to compute hash in database for comparison
    # This matches the exact computation used by the application
    query = text(
        f"""
        SELECT
            id::text AS record_id,
            owner_api_key,
            owner_api_key_hash,
            encode(digest(owner_api_key, 'sha256'), 'hex') AS computed_hash
        FROM {table_name}
        WHERE owner_api_key IS NOT NULL
        ORDER BY created_at DESC
        """
    )

    result = await session.execute(query)
    rows = result.fetchall()

    total_checked = len(rows)
    mismatches: list[str] = []

    for row in rows:
        record_id = row.record_id
        stored_hash = row.owner_api_key_hash
        computed_hash = row.computed_hash

        if stored_hash != computed_hash:
            mismatches.append(
                f"  {table_name}.id={record_id}: "
                f"stored={stored_hash or 'NULL'}, computed={computed_hash}"
            )

    return total_checked, len(mismatches), mismatches


async def verify_all_tables() -> int:
    """Verify hash consistency across all tables.

    Returns:
        Exit code (0 if all match, 1 if mismatches found).
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set", file=sys.stderr)
        print(
            "USAGE: export DATABASE_URL='postgresql://...' && uv run python scripts/verify_hash_consistency.py",
            file=sys.stderr,
        )
        return 1

    # Convert to async URL if needed
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print(f"Connecting to database: {database_url.split('@')[1]}")  # Hide credentials
    engine = create_async_engine(database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            # Verify sessions table
            print("\n[1/2] Verifying sessions table...")
            sessions_total, sessions_mismatches, sessions_details = (
                await verify_table_hashes(session, "sessions")
            )
            print(f"  Total records checked: {sessions_total}")
            print(f"  Records with matching hashes: {sessions_total - sessions_mismatches}")
            print(f"  Records with mismatches: {sessions_mismatches}")

            if sessions_details:
                print("\n  MISMATCHES FOUND:")
                for detail in sessions_details:
                    print(detail)

            # Verify assistants table
            print("\n[2/2] Verifying assistants table...")
            assistants_total, assistants_mismatches, assistants_details = (
                await verify_table_hashes(session, "assistants")
            )
            print(f"  Total records checked: {assistants_total}")
            print(
                f"  Records with matching hashes: {assistants_total - assistants_mismatches}"
            )
            print(f"  Records with mismatches: {assistants_mismatches}")

            if assistants_details:
                print("\n  MISMATCHES FOUND:")
                for detail in assistants_details:
                    print(detail)

            # Summary
            total_mismatches = sessions_mismatches + assistants_mismatches
            total_checked = sessions_total + assistants_total

            print("\n" + "=" * 70)
            print("SUMMARY")
            print("=" * 70)
            print(f"Total records checked: {total_checked}")
            print(f"Records with matching hashes: {total_checked - total_mismatches}")
            print(f"Records with mismatches: {total_mismatches}")

            if total_mismatches > 0:
                print("\n❌ VERIFICATION FAILED - DATA CORRUPTION DETECTED")
                print(f"Found {total_mismatches} hash mismatch(es) across tables.")
                print("\nACTION REQUIRED:")
                print("1. DO NOT PROCEED with Phase 3 deployment (dropping plaintext column)")
                print("2. Investigate root cause of hash mismatches")
                print("3. Run Phase 1 migration again to recompute hashes")
                print("4. Re-run this script to verify fixes")
                return 1

            print("\n✅ VERIFICATION PASSED - ALL HASHES MATCH")
            print("Database is consistent and ready for Phase 3 deployment.")
            return 0

    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1
    finally:
        await engine.dispose()


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    return asyncio.run(verify_all_tables())


if __name__ == "__main__":
    sys.exit(main())

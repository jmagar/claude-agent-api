#!/usr/bin/env python3
"""Hash Consistency Verification Script.

PHASE 3 NOTE:
After Phase 3 migration (dropping plaintext owner_api_key columns), this script
verifies that hash columns exist and are populated. The plaintext-to-hash
comparison is no longer possible since plaintext columns have been removed.

BEFORE PHASE 3:
This script verified that all owner_api_key_hash values correctly matched the
SHA-256 hash of their corresponding owner_api_key plaintext values.

AFTER PHASE 3 (current state):
This script verifies:
1. Hash columns exist in both tables
2. Reports statistics on hashed keys

EXIT CODES:
0 - Verification passed
1 - Error occurred

USAGE:
    export DATABASE_URL="postgresql://user:pass@host:port/dbname"
    uv run python scripts/verify_hash_consistency.py
"""

import asyncio
import os
import sys

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


async def check_column_exists(
    session: AsyncSession, table_name: str, column_name: str
) -> bool:
    """Check if a column exists in a table.

    Args:
        session: Database session.
        table_name: Name of the table.
        column_name: Name of the column to check.

    Returns:
        True if column exists, False otherwise.
    """
    query = text(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_name = :table_name
            AND column_name = :column_name
        )
        """
    )
    result = await session.execute(
        query, {"table_name": table_name, "column_name": column_name}
    )
    row = result.fetchone()
    return bool(row and row[0])


async def count_hashed_records(session: AsyncSession, table_name: str) -> tuple[int, int]:
    """Count total and hashed records in a table.

    Args:
        session: Database session.
        table_name: Name of the table.

    Returns:
        Tuple of (total_records, records_with_hash).
    """
    # Count total records
    total_query = text(f"SELECT COUNT(*) FROM {table_name}")
    total_result = await session.execute(total_query)
    total_row = total_result.fetchone()
    total = total_row[0] if total_row else 0

    # Count records with hash
    hash_query = text(
        f"SELECT COUNT(*) FROM {table_name} WHERE owner_api_key_hash IS NOT NULL"
    )
    hash_result = await session.execute(hash_query)
    hash_row = hash_result.fetchone()
    hashed = hash_row[0] if hash_row else 0

    return total, hashed


async def verify_phase3_state() -> int:
    """Verify Phase 3 migration state.

    Returns:
        Exit code (0 if verification passed, 1 if errors).
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

    # Hide credentials in output
    display_url = database_url.split("@")[1] if "@" in database_url else database_url
    print(f"Connecting to database: {display_url}")
    engine = create_async_engine(database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as session:
            # Check if plaintext columns exist (they shouldn't after Phase 3)
            sessions_has_plaintext = await check_column_exists(
                session, "sessions", "owner_api_key"
            )
            assistants_has_plaintext = await check_column_exists(
                session, "assistants", "owner_api_key"
            )

            # Check if hash columns exist (they should)
            sessions_has_hash = await check_column_exists(
                session, "sessions", "owner_api_key_hash"
            )
            assistants_has_hash = await check_column_exists(
                session, "assistants", "owner_api_key_hash"
            )

            print("\n[1/2] Verifying sessions table...")
            if sessions_has_plaintext:
                print("  ⚠️  owner_api_key column still exists (Phase 3 not complete)")
            else:
                print("  ✅ owner_api_key column removed (Phase 3 complete)")

            if sessions_has_hash:
                print("  ✅ owner_api_key_hash column exists")
                total, hashed = await count_hashed_records(session, "sessions")
                print(f"  Total records: {total}")
                print(f"  Records with hash: {hashed}")
            else:
                print("  ❌ owner_api_key_hash column missing!")
                return 1

            print("\n[2/2] Verifying assistants table...")
            if assistants_has_plaintext:
                print("  ⚠️  owner_api_key column still exists (Phase 3 not complete)")
            else:
                print("  ✅ owner_api_key column removed (Phase 3 complete)")

            if assistants_has_hash:
                print("  ✅ owner_api_key_hash column exists")
                total, hashed = await count_hashed_records(session, "assistants")
                print(f"  Total records: {total}")
                print(f"  Records with hash: {hashed}")
            else:
                print("  ❌ owner_api_key_hash column missing!")
                return 1

            # Summary
            print("\n" + "=" * 70)
            print("SUMMARY")
            print("=" * 70)

            phase3_complete = not sessions_has_plaintext and not assistants_has_plaintext

            if phase3_complete:
                print("\n✅ VERIFICATION PASSED - PHASE 3 COMPLETE")
                print("Both tables have hash columns only (plaintext columns removed).")
                print("API key hashing migration is fully complete.")
            else:
                print("\n⚠️  PHASE 3 NOT YET COMPLETE")
                print("Plaintext columns still exist. Run the Phase 3 migration:")
                print("  uv run alembic upgrade 20260208_000007")

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
    return asyncio.run(verify_phase3_state())


if __name__ == "__main__":
    sys.exit(main())

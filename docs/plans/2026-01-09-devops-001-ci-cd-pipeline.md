# DEVOPS-001 CI/CD Pipeline Implementation Plan

> **Organization Note:** When this plan is fully implemented and verified, move this file to `docs/plans/complete/` to keep the plans folder organized.

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a CI pipeline that runs linting, type checking, and tests automatically on pushes and PRs.

**Architecture:** Use GitHub Actions with `uv` to install dependencies and run `ruff`, `mypy`, and `pytest`. Keep the workflow minimal and aligned with existing `Makefile` commands.

**Tech Stack:** GitHub Actions, Python 3.11, uv, Ruff, mypy, pytest.

---

### Task 1: Add GitHub Actions workflow for CI

**Files:**
- Create: `.github/workflows/ci.yml`

**Implementation:**

Create `.github/workflows/ci.yml` with a complete CI pipeline that:
1. Starts PostgreSQL and Redis services (required for tests)
2. Installs dependencies with uv
3. Runs database migrations
4. Executes linting, type checking, and fast test suite

```yaml
name: CI

on:
  push:
    branches: ["main"]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      API_KEY: "ci-test-key"
      DEBUG: "true"
      CORS_ORIGINS: "[\"http://localhost:3000\"]"
      DATABASE_URL: "postgresql+asyncpg://postgres:postgres@localhost:5432/claude_agent_test"
      REDIS_URL: "redis://localhost:6379/0"

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: claude_agent_test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Set up uv
        uses: astral-sh/setup-uv@v5
        with:
          enable-cache: true

      - name: Install dependencies
        run: uv sync

      - name: Run migrations
        run: uv run alembic upgrade head

      - name: Lint
        run: uv run ruff check .

      - name: Type check
        run: uv run mypy apps/api tests/

      - name: Test
        run: uv run pytest tests/unit tests/contract -v
```

**Verification:**

```bash
# Verify file was created
ls -la .github/workflows/ci.yml

# Verify services are configured
grep -A5 "services:" .github/workflows/ci.yml

# Verify migration step exists
grep "alembic upgrade head" .github/workflows/ci.yml
```

**Commit:**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions pipeline with PostgreSQL and Redis services"
```

### Task 2: Document the new CI pipeline

**Files:**
- Modify: `README.md`
- Modify: `.docs/audit-summary.md`

**Implementation:**

Add CI documentation to README.md after the "Development" section:

```markdown
## CI/CD

GitHub Actions runs automated checks on every push and pull request:

- **Linting**: Ruff checks code style and common errors
- **Type Checking**: mypy verifies type safety with strict mode
- **Testing**: Fast test suite (unit + contract tests) with PostgreSQL and Redis

The CI pipeline ensures code quality and catches issues before merge. All checks must pass before merging to `main`.

### Branch Protection

To enforce CI checks in your repository:
1. Go to Settings > Branches > Add rule
2. Branch name pattern: `main`
3. Enable "Require status checks to pass before merging"
4. Select: `test` (the job name from ci.yml)
```

Update `.docs/audit-summary.md` to mark DEVOPS-001 as fixed. Find the section mentioning missing CI/CD or Dockerfile issues and add:

```markdown
**DEVOPS-001: CI/CD Pipeline**
**Status**: ✅ Fixed
**Date**: 2026-01-09
**Details**: GitHub Actions pipeline added with:
- PostgreSQL and Redis services for test isolation
- Database migrations before tests
- Ruff linting, mypy type checking
- Fast test suite (unit + contract tests)
- Proper dependency caching with uv
```

**Verification:**

```bash
# Check README has CI section
grep -A5 "## CI/CD" README.md

# Check audit summary updated
grep -A3 "DEVOPS-001" .docs/audit-summary.md
```

**Commit:**

```bash
git add README.md .docs/audit-summary.md
git commit -m "docs: document CI pipeline and mark DEVOPS-001 as fixed"
```

---

**Notes:**
- This plan creates infrastructure-as-code (GitHub Actions workflow), not application features
- Verification steps confirm file creation and content, not behavior testing
- Fast test suite (unit + contract) used to keep CI builds under 2 minutes
- PostgreSQL and Redis services run in containers during CI for test isolation

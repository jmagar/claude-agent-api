# DevOps Quick Wins Checklist

**Date:** 02:18:06 AM | 01/10/2026
**Purpose:** Immediate, high-impact improvements requiring <4 hours total effort

---

## Quick Wins Summary

**Total effort:** ~3-4 hours
**Total impact:** Prevent broken builds, improve resilience, increase confidence

| # | Task | Effort | Impact | Priority |
|---|------|--------|--------|----------|
| 1 | Create .dockerignore | 30 min | Faster builds, smaller images | HIGH |
| 2 | Add restart policies | 15 min | Auto-recovery from crashes | HIGH |
| 3 | Add integration tests to CI | 1 hour | Catch integration bugs | HIGH |
| 4 | Add Docker build to CI | 1 hour | Verify builds succeed | HIGH |
| 5 | Setup branch protection | 30 min | Require CI pass + review | MEDIUM |

---

## Task 1: Create .dockerignore

**Effort:** 30 minutes
**Impact:** Faster Docker builds (40-60% reduction), smaller images
**Priority:** HIGH

### Implementation

Create `/mnt/cache/workspace/claude-agent-api/.dockerignore`:

```dockerfile
# Version control
.git/
.github/

# Virtual environments
.venv/
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Testing
.cache/
.pytest_cache/
.mypy_cache/
.ruff_cache/
coverage.json
.coverage
htmlcov/

# Documentation
docs/
.docs/
*.md
!README.md

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Environment files
.env
.env.*
!.env.example

# Build artifacts
dist/
build/
*.egg-info/
__pypackages__/

# Logs
*.log

# OS files
.DS_Store
Thumbs.db
```

### Verification

```bash
# Before:
docker build . 2>&1 | grep "Sending build context"
# Expected: ~50-100MB

# After:
docker build . 2>&1 | grep "Sending build context"
# Expected: ~5-10MB (90% reduction)
```

### Files to Update

- [x] Create `.dockerignore`

**Status:** ⬜ NOT STARTED

---

## Task 2: Add Restart Policies

**Effort:** 15 minutes
**Impact:** Services auto-recover from crashes, reduce downtime
**Priority:** HIGH

### Implementation

Update `/mnt/cache/workspace/claude-agent-api/docker-compose.yaml`:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: claude-agent-postgres
    restart: unless-stopped  # ← ADD THIS
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: claude_agent
    ports:
      - "53432:5432"
    volumes:
      - claude_agent_postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: claude-agent-redis
    restart: unless-stopped  # ← ADD THIS
    command: redis-server --appendonly yes
    ports:
      - "53380:6379"
    volumes:
      - claude_agent_redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  claude_agent_postgres_data:
  claude_agent_redis_data:
```

### Verification

```bash
# Test restart policy:
docker compose up -d
docker stop claude-agent-postgres
sleep 2
docker ps | grep claude-agent-postgres  # Should be running again

# Verify policy set:
docker inspect claude-agent-postgres | grep -A 5 RestartPolicy
# Expected: "Name": "unless-stopped"
```

### Files to Update

- [x] `docker-compose.yaml` (add `restart: unless-stopped` to both services)

**Status:** ⬜ NOT STARTED

---

## Task 3: Add Integration Tests to CI

**Effort:** 1 hour
**Impact:** Catch integration bugs before merge, increase confidence
**Priority:** HIGH

### Implementation

Update `/mnt/cache/workspace/claude-agent-api/.github/workflows/ci.yml`:

```yaml
# BEFORE (line 68-69):
- name: Test
  run: uv run pytest tests/unit tests/contract -v

# AFTER:
- name: Test
  run: uv run pytest tests/unit tests/contract tests/integration -v --cov=apps/api --cov-report=term-missing --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v4
  with:
    files: ./coverage.xml
    fail_ci_if_error: false
```

### Verification

```bash
# Local test:
uv run pytest tests/integration -v
# Should pass all integration tests (currently 777 total tests)

# CI test:
git commit -m "ci: add integration tests to pipeline"
git push
# Check GitHub Actions run
```

### Expected Results

- ✅ All 777 tests run in CI
- ✅ Coverage reported (~84%)
- ⏱️ CI time increases by ~30 seconds
- ✅ Integration bugs caught before merge

### Files to Update

- [x] `.github/workflows/ci.yml` (line 68-69)

**Status:** ⬜ NOT STARTED

---

## Task 4: Add Docker Build to CI

**Effort:** 1 hour
**Impact:** Verify Dockerfile builds successfully, catch breaking changes
**Priority:** HIGH

### Implementation

Add to `/mnt/cache/workspace/claude-agent-api/.github/workflows/ci.yml` (after Test step):

```yaml
- name: Build Docker image
  run: docker build . --tag claude-agent-api:ci-${{ github.sha }}

- name: Test Docker image
  run: |
    # Start container with test environment
    docker run -d \
      --name test-api \
      --network host \
      -e API_KEY=ci-test-key \
      -e DATABASE_URL="${{ env.DATABASE_URL }}" \
      -e REDIS_URL="${{ env.REDIS_URL }}" \
      -e DEBUG=true \
      claude-agent-api:ci-${{ github.sha }}

    # Wait for health check (max 30s)
    echo "Waiting for API to be healthy..."
    timeout 30 bash -c 'until curl -f http://localhost:54000/health 2>/dev/null; do echo -n "."; sleep 1; done'
    echo "✓ API healthy"

    # Verify health response
    curl -f http://localhost:54000/health | jq .

    # Cleanup
    docker stop test-api
    docker rm test-api

- name: Scan Docker image for vulnerabilities
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: claude-agent-api:ci-${{ github.sha }}
    format: 'sarif'
    output: 'trivy-results.sarif'
    severity: 'CRITICAL,HIGH'
    exit-code: '0'  # Don't fail on vulnerabilities (yet)

- name: Upload Trivy results
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: 'trivy-results.sarif'
```

### Verification

```bash
# Local test:
docker build . --tag claude-agent-api:test
docker run -d --name test-api \
  --network host \
  -e API_KEY=test \
  -e DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:53432/claude_agent_test \
  -e REDIS_URL=redis://localhost:53380/0 \
  claude-agent-api:test

# Wait and check health
sleep 10
curl http://localhost:54000/health

# Cleanup
docker stop test-api && docker rm test-api
```

### Expected Results

- ✅ Docker build succeeds in CI
- ✅ Health check passes
- ✅ Vulnerability scan runs (informational)
- ⏱️ CI time increases by ~2-3 minutes

### Files to Update

- [x] `.github/workflows/ci.yml` (add Docker build/test steps after line 69)

**Status:** ⬜ NOT STARTED

---

## Task 5: Setup Branch Protection Rules

**Effort:** 30 minutes
**Impact:** Enforce CI passing and code review, prevent broken code from merging
**Priority:** MEDIUM

### Implementation

GitHub Repository Settings → Branches → Add rule for `main`:

#### Protection Rules

- [x] **Require a pull request before merging**
  - [x] Require approvals: 1
  - [x] Dismiss stale pull request approvals when new commits are pushed
  - [x] Require review from Code Owners (optional)

- [x] **Require status checks to pass before merging**
  - [x] Require branches to be up to date before merging
  - [x] Status checks required:
    - `test` (CI job)
    - `lint` (if separate job)
    - `type-check` (if separate job)

- [x] **Require conversation resolution before merging**

- [ ] **Require signed commits** (optional, recommended)

- [x] **Include administrators** (enforce rules for admins too)

- [x] **Do not allow bypassing the above settings**

#### Additional Settings

- [x] **Allow squash merging** (recommended)
- [ ] **Allow merge commits** (optional)
- [ ] **Allow rebase merging** (optional)
- [x] **Automatically delete head branches** (cleanup)

### Verification

```bash
# Test protection rules:
git checkout -b test-protection
echo "test" > test.txt
git add test.txt
git commit -m "test: branch protection"
git push origin test-protection

# Create PR on GitHub, try to merge without CI passing
# Expected: Merge blocked until CI passes
```

### Configuration

1. Go to: `https://github.com/YOUR_ORG/claude-agent-api/settings/branches`
2. Click "Add rule"
3. Branch name pattern: `main`
4. Apply settings above
5. Click "Create"

**Status:** ⬜ NOT STARTED

---

## Implementation Order

**Recommended sequence:**

1. **Task 1: .dockerignore** (30 min)
   - No dependencies
   - Immediate build speed improvement

2. **Task 2: Restart policies** (15 min)
   - No dependencies
   - Immediate resilience improvement

3. **Task 4: Docker build in CI** (1 hour)
   - Depends on Task 1 for faster builds
   - Verifies Docker setup before adding to CI

4. **Task 3: Integration tests in CI** (1 hour)
   - Independent of Docker changes
   - Increases confidence for next tasks

5. **Task 5: Branch protection** (30 min)
   - Requires CI pipeline to be stable
   - Enforces all previous improvements

**Total time:** ~3 hours 15 minutes

---

## Verification Checklist

After completing all tasks:

- [ ] `.dockerignore` file exists
- [ ] Docker build context reduced by >80%
- [ ] Restart policies configured on postgres + redis
- [ ] Integration tests run in CI pipeline
- [ ] Docker build succeeds in CI
- [ ] Branch protection rules active on `main`
- [ ] CI must pass before merge allowed
- [ ] Code review required before merge

---

## Expected Outcomes

**Before Quick Wins:**
- ❌ Large Docker build context (~50-100MB)
- ❌ Services don't auto-recover from crashes
- ❌ Integration tests not run in CI
- ❌ Docker builds not verified in CI
- ❌ Can merge without CI passing

**After Quick Wins:**
- ✅ Small Docker build context (~5-10MB) - 90% reduction
- ✅ Services auto-restart on failure
- ✅ All 777 tests run in CI (unit + contract + integration)
- ✅ Docker build verified before merge
- ✅ CI must pass + code review required

**Impact Summary:**
- 🚀 40-60% faster Docker builds
- 🛡️ Auto-recovery from crashes
- 🔍 Integration bugs caught before merge
- 🏗️ Docker build breakage prevented
- 🔒 Code quality enforced

---

## Next Steps After Quick Wins

Once quick wins are complete, proceed to:

1. **Metrics endpoint** (Priority 1) - 4-6 hours
2. **Log aggregation** (Priority 1) - 8-12 hours
3. **Alerting** (Priority 1) - 4-8 hours
4. **Deployment pipeline** (Priority 1) - 16-24 hours

See full roadmap in: `.docs/cicd-devops-assessment-2026-01-10.md`

---

**Checklist created:** 02:18:06 AM | 01/10/2026
**Estimated completion time:** 3-4 hours
**Next review:** After all tasks completed

# Deployment Log

This file tracks all deployments of the Claude Agent API service.

**Format:** Timestamp | Environment | Version | Services | Notes

---

## 2026-01-10 02:09:16 | Development

**Deployment Type:** Initial Development Setup
**Version:** 1.0.0-dev
**Branch:** chore/bugsweep
**Commit:** 9da6859

**Services Deployed:**
- **API Server:** Port 54000 (Uvicorn development server with --reload)
- **PostgreSQL:** Port 53432 (Docker container)
- **Redis:** Port 53380 (Docker container)

**Database Migrations:**
- Applied: `20260107_000001_initial_sessions.py`
- Status: Up-to-date

**Configuration:**
- Environment: Development
- Debug mode: Enabled
- CORS: `http://localhost:3000`
- Rate limiting: Enabled (10 queries/min)
- File checkpointing: Disabled
- Trust proxy headers: Disabled

**Infrastructure:**
- Container host: code-server container on Tailscale IP 100.120.242.29
- Database URL: `postgresql+asyncpg://postgres:postgres@host.docker.internal:53432/claude_agent`
- Redis URL: `redis://host.docker.internal:53380/0`

**Notes:**
- Development environment inside code-server container
- Services deployed to container host via Docker Compose
- API connects to services via `host.docker.internal` hostname
- Authentication: API key via `X-API-Key` header
- Claude Max subscription auth used (ANTHROPIC_API_KEY not set)

**Issues:**
- None

**Deployed By:** Claude Code (automated)
**Verified By:** N/A (no production deployment yet)

---

## Future Deployments

Template for future entries:

```markdown
## YYYY-MM-DD HH:MM:SS | Environment

**Deployment Type:** (Initial / Update / Rollback / Hotfix)
**Version:** X.Y.Z
**Branch:** branch-name
**Commit:** commit-hash

**Services Deployed:**
- **API Server:** Port XXXXX
- **PostgreSQL:** Port XXXXX
- **Redis:** Port XXXXX

**Database Migrations:**
- Applied: migration-name.py
- Status: Up-to-date / Rolled back to XXXXX

**Configuration Changes:**
- List any environment variable changes
- List any feature flag changes

**Infrastructure Changes:**
- List any infrastructure updates

**Notes:**
- Any relevant deployment notes
- Performance observations
- Issues encountered

**Deployed By:** Name
**Verified By:** Name
**Rollback Plan:** Steps to rollback if needed
```

---

## Rollback Procedures

### Database Rollback

```bash
# Downgrade to specific revision
uv run alembic downgrade <revision>

# Downgrade one step
uv run alembic downgrade -1

# Check current version
uv run alembic current
```

### Service Rollback

```bash
# Stop current version
docker compose down

# Checkout previous version
git checkout <previous-commit>

# Rebuild and restart
docker compose up -d --build

# Verify health
curl http://localhost:54000/api/v1/health
```

### Rollback Checklist

- [ ] Notify team of rollback in progress
- [ ] Stop accepting new requests (set maintenance mode if available)
- [ ] Downgrade database migrations (if needed)
- [ ] Deploy previous version of services
- [ ] Verify health endpoints
- [ ] Check logs for errors
- [ ] Resume traffic
- [ ] Document rollback reason and steps in this log

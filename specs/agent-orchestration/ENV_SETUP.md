# Environment Setup Guide

Complete guide to configuring environment variables for the Claude Agent API.

## Quick Start

```bash
# 1. Copy template
cp .env.example .env

# 2. Edit required variables
vim .env  # Or your preferred editor

# 3. Verify external services
curl http://100.74.16.82:52000/health

# 4. Start infrastructure
docker compose up -d
```

---

## Required Variables

These variables **must** be set for the API to function:

| Variable | Purpose | Example Value |
|----------|---------|---------------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:54432/claude_agent` |
| `REDIS_URL` | Redis connection string | `redis://localhost:54379` |
| `API_KEY` | Client authentication key | `your-secure-api-key-here` |
| `LLM_API_KEY` | LLM provider API key (memory extraction) | `sk-proj-...` |
| `LLM_BASE_URL` | LLM provider base URL | `https://cli-api.tootie.tv/v1` |
| `LLM_MODEL` | Model name for memory extraction | `gemini-3-flash-preview` |
| `TEI_URL` | Text Embeddings Inference endpoint | `http://100.74.16.82:52000` |
| `QDRANT_URL` | Qdrant vector database URL | `http://localhost:53333` |
| `NEO4J_URL` | Neo4j graph database URL | `bolt://localhost:54687` |
| `NEO4J_USERNAME` | Neo4j authentication username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j authentication password | `neo4jpassword` |

---

## Optional Variables (Has Defaults)

These variables have sensible defaults and can be omitted:

| Variable | Default | Purpose |
|----------|---------|---------|
| `API_HOST` | `0.0.0.0` | Server bind address |
| `API_PORT` | `54000` | Server port |
| `DEBUG` | `false` | Enable debug mode (enables `/docs`) |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `CORS_ORIGINS` | `http://localhost:3000` | Allowed CORS origins (comma-separated) |
| `TEI_EMBEDDING_DIMS` | `1024` | Embedding vector dimensions |
| `QDRANT_COLLECTION` | `mem0_memories` | Qdrant collection name |
| `NEO4J_DATABASE` | `neo4j` | Neo4j database name |
| `HEARTBEAT_INTERVAL` | `30` | Agent heartbeat interval (seconds) |
| `HEARTBEAT_TIMEOUT` | `90` | Agent heartbeat timeout (seconds) |
| `HEARTBEAT_ENABLED` | `true` | Enable heartbeat monitoring |
| `STRUCTURED_LOGGING` | `true` | Use structured JSON logs |

---

## Optional Variables (Feature-Specific)

These variables enable optional features:

| Variable | Purpose | Required For |
|----------|---------|--------------|
| `GOTIFY_URL` | Gotify server URL | Push notifications |
| `GOTIFY_TOKEN` | Gotify app token | Push notifications |
| `GOTIFY_ENABLED` | Enable Gotify integration | Push notifications |
| `SYNAPSE_MCP_ENABLED` | Enable synapse-mcp server | Docker/SSH management |
| `SYNAPSE_SSH_HOST` | SSH target hostname | synapse-mcp |
| `SYNAPSE_SSH_PORT` | SSH port | synapse-mcp |
| `SYNAPSE_SSH_USER` | SSH username | synapse-mcp |
| `SYNAPSE_SSH_KEY_PATH` | SSH private key path | synapse-mcp |
| `TEST_DATABASE_URL` | Test database connection | Running tests |
| `CLAUDE_CODE_ENABLE_SDK_FILE_CHECKPOINTING` | Enable SDK file checkpointing | Claude SDK features |

---

## External Dependencies

### Text Embeddings Inference (TEI)

**Location:** `http://100.74.16.82:52000` (external service)
**Model:** Qwen/Qwen3-Embedding-0.6B (1024 dimensions)
**Purpose:** Generates embeddings for Mem0 memory system

**Verification:**
```bash
# Check TEI health
curl http://100.74.16.82:52000/health

# Expected response: {"status":"ok"}
```

**Troubleshooting:**
- If unreachable, verify network connectivity to host `100.74.16.82`
- Ensure firewall allows traffic on port `52000`
- Contact infrastructure team if TEI is down

### Gotify (Optional)

**Purpose:** Push notifications for long-running tasks and user input required
**Setup:** Deploy your own Gotify instance or use hosted service
**Documentation:** https://gotify.net/

**Configuration:**
1. Deploy Gotify server
2. Create application and get token
3. Set `GOTIFY_URL` and `GOTIFY_TOKEN` in `.env`
4. Set `GOTIFY_ENABLED=true`

---

## Troubleshooting

### Connection Refused Errors

**Symptom:** `Connection refused` when starting API

**Solutions:**
```bash
# 1. Verify infrastructure is running
docker compose ps

# 2. Start missing services
docker compose up -d

# 3. Check port conflicts
ss -tuln | grep -E '54432|54379|54687|53333'

# 4. Verify .env matches docker-compose ports
grep -E 'DATABASE_URL|REDIS_URL|NEO4J_URL' .env
```

### TEI Unavailable

**Symptom:** `Failed to connect to TEI at http://100.74.16.82:52000`

**Solutions:**
```bash
# 1. Verify TEI is reachable
curl -v http://100.74.16.82:52000/health

# 2. Check network connectivity
ping 100.74.16.82

# 3. Verify firewall rules
# Contact infrastructure team if issues persist
```

### Neo4j Authentication Failed

**Symptom:** `Authentication failed` or `Invalid credentials`

**Solutions:**
```bash
# 1. Verify credentials match docker-compose
grep NEO4J docker-compose.yaml
grep NEO4J .env

# 2. Reset Neo4j password (if needed)
docker compose down neo4j
docker volume rm claude-agent-api_neo4j_data
docker compose up -d neo4j

# 3. Wait for Neo4j startup (check logs)
docker compose logs -f neo4j
```

### Memory Extraction Failures

**Symptom:** `LLM provider error` or `Memory extraction failed`

**Solutions:**
```bash
# 1. Verify LLM API key is valid
curl -H "Authorization: Bearer $LLM_API_KEY" \
  https://cli-api.tootie.tv/v1/models

# 2. Check LLM base URL is correct
grep LLM_BASE_URL .env

# 3. Verify model name is available
# Contact LLM provider if model is deprecated
```

---

## Security Notes

### Credential Management

1. **Never commit `.env` to version control**
   - `.env` is in `.gitignore` by default
   - Only commit `.env.example` template

2. **Rotate API keys regularly**
   - Change `API_KEY` periodically
   - Update clients after rotation

3. **Use strong passwords**
   - `NEO4J_PASSWORD` should be 16+ characters
   - Mix uppercase, lowercase, numbers, symbols

4. **Restrict network access**
   - Use firewall rules to limit database access
   - Consider VPN for external services (TEI, Gotify)

### Production Hardening

```bash
# 1. Disable debug mode
DEBUG=false

# 2. Restrict CORS origins
CORS_ORIGINS=https://yourdomain.com

# 3. Use TLS for databases (production)
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
NEO4J_URL=neo4j+s://host:7687  # Bolt over TLS

# 4. Enable structured logging
STRUCTURED_LOGGING=true
LOG_LEVEL=WARNING  # Reduce verbosity in production
```

### Environment Isolation

Use separate `.env` files for different environments:

```bash
# Development
.env.development

# Staging
.env.staging

# Production
.env.production
```

Load environment-specific file:
```bash
# Development
cp .env.development .env

# Production
cp .env.production .env
```

---

## Next Steps

After configuring `.env`:

1. **Start Infrastructure**: `docker compose up -d`
2. **Run Migrations**: `uv run alembic upgrade head`
3. **Start API**: `make dev` or `uv run uvicorn apps.api.main:app --reload --port 54000`
4. **Verify Health**: `curl http://localhost:54000/health`
5. **Run Tests**: `uv run pytest`

For API documentation, enable debug mode and visit:
- Swagger UI: http://localhost:54000/docs
- ReDoc: http://localhost:54000/redoc

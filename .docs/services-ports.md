# Services and Ports Registry

**Purpose:** Central registry of all service port assignments for the Claude Agent API project.

**Port Range:** 53000-54999 (avoiding common ports 80, 443, 3000, 5000, 8000, 8080)

**Last Updated:** 2026-01-29 06:23:34

---

## Active Services

| Service | Port | Protocol | Status | Environment | Notes |
|---------|------|----------|--------|-------------|-------|
| **API Server** | 54000 | HTTP | Active | Development | FastAPI + Uvicorn |
| **PostgreSQL** | 54432 | TCP | Active | Development | Primary database |
| **Redis** | 54379 | TCP | Active | Development | Cache + Pub/Sub |

---

## Port Assignment Rules

1. **High Ports Only:** Use ports 53000+ to avoid conflicts with common services
2. **Sequential Assignment:** Assign ports sequentially (53000, 53001, 53002...)
3. **Check Before Assigning:** Always verify port availability:
   ```bash
   ss -tuln | grep :PORT
   lsof -i :PORT
   ```
4. **Document Immediately:** Update this file when assigning new ports
5. **Avoid Standard Ports:**
   - Web: 80, 443, 3000, 8000, 8080, 8443, 9000
   - Databases: 5432 (Postgres), 3306 (MySQL), 27017 (MongoDB), 6379 (Redis)
   - Message Queues: 5672 (RabbitMQ), 9092 (Kafka)
   - Other: 22 (SSH), 25 (SMTP), 53 (DNS)

---

## Port Details

### API Server (54000)

- **Service:** FastAPI application
- **Process:** Uvicorn ASGI server
- **Deployment:** Docker container / systemd service
- **Health Check:** `GET http://localhost:54000/api/v1/health`
- **TLS:** Not configured (use reverse proxy in production)
- **Connections:** Max 500 per worker (configurable via `--limit-concurrency`)

**Configuration:**
```bash
# Development
uvicorn apps.api.main:app --host 0.0.0.0 --port 54000 --reload

# Production
uvicorn apps.api.main:app --host 0.0.0.0 --port 54000 --workers 4
```

---

### PostgreSQL (54432)

- **Service:** PostgreSQL 15+
- **Process:** postgres
- **Deployment:** Docker container
- **Health Check:** `pg_isready -h localhost -p 54432`
- **TLS:** Disabled (local development)
- **Connections:** Max 100 (default PostgreSQL limit)

**Configuration:**
```yaml
# docker-compose.yaml
services:
  postgres:
    image: postgres:15
    ports:
      - "54432:5432"
    environment:
      POSTGRES_DB: claude_agent
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
```

**Connection String:**
```bash
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:54432/claude_agent
```

---

### Redis (54379)

- **Service:** Redis 7+
- **Process:** redis-server
- **Deployment:** Docker container
- **Health Check:** `redis-cli -p 54379 ping`
- **TLS:** Disabled (local development)
- **Connections:** Max 10,000 (default Redis limit)

**Configuration:**
```yaml
# docker-compose.yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "54379:6379"
```

**Connection String:**
```bash
REDIS_URL=redis://localhost:54379/0
```

---

## Reserved Ports (Planned Services)

| Port | Service | Status | Purpose |
|------|---------|--------|---------|
| 54001 | SSE Worker | Planned | Dedicated SSE streaming worker |
| 54002 | Monitoring | Planned | Prometheus metrics endpoint |

---

## Port Conflict Resolution

If a port is already in use:

1. **Check what's using it:**
   ```bash
   lsof -i :PORT
   ss -tuln | grep :PORT
   ```

2. **Verify it's not a required service:**
   - Check this registry
   - Check team communication

3. **Auto-increment if conflict:**
   ```bash
   # If 54000 is taken, use 54001
   # Document the new port in this file
   ```

4. **Never force-kill existing services** without verification

---

## Environment-Specific Ports

### Development
- API: 54000
- PostgreSQL: 54432
- Redis: 54379

### Staging (Future)
- API: TBD
- PostgreSQL: TBD
- Redis: TBD

### Production (Future)
- API: TBD (behind reverse proxy on 443)
- PostgreSQL: TBD (internal only)
- Redis: TBD (internal only)

---

## Network Topology

```
┌─────────────────────────────────────────┐
│ Container Host (100.120.242.29)        │
│                                         │
│  ┌────────────┐   ┌──────────────┐     │
│  │ PostgreSQL │   │    Redis     │     │
│  │  :54432    │   │    :54379    │     │
│  └─────▲──────┘   └──────▲───────┘     │
│        │                 │              │
│        └────────┬────────┘              │
│                 │                       │
│        ┌────────▼────────┐              │
│        │   API Server    │              │
│        │     :54000      │              │
│        └─────────────────┘              │
└─────────────────────────────────────────┘
                 │
                 │ (External Access)
                 ▼
        ┌─────────────────┐
        │   Developers    │
        └─────────────────┘
```

---

## Maintenance Notes

### Port Change Procedure

1. **Update this file** with new port assignment
2. **Update `.env.example`** with new default
3. **Update `docker-compose.yaml`** if service is containerized
4. **Update `CLAUDE.md`** port assignments section
5. **Update `README.md`** port assignments table
6. **Update deployment log** with port change reason
7. **Notify team** via communication channel

### Port Audit

Last audit: 2026-01-10
Next audit: 2026-02-10 (monthly)

**Audit Checklist:**
- [ ] Verify all documented ports are in use
- [ ] Check for undocumented services on high ports
- [ ] Verify port ranges don't conflict with new services
- [ ] Update reserved ports list if needed

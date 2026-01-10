FROM python:3.11-slim

WORKDIR /app

# Pin uv version and disable pip cache
RUN pip install --no-cache-dir uv==0.5.11

# Install dependencies first (better layer caching)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application code
COPY apps/ ./apps/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Create non-root user and set ownership
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check - validates app and dependencies are responding
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:54000/health').read()"

# Start application only
# NOTE: Run migrations separately before deployment:
#   docker run --rm <image> uv run alembic upgrade head
CMD ["uv", "run", "uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "54000"]

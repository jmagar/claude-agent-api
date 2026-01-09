FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY apps/ ./apps/
COPY alembic/ ./alembic/
COPY alembic.ini ./

CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn apps.api.main:app --host 0.0.0.0 --port 54000"]

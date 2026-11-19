FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1 MPLBACKEND=Agg MPLCONFIGDIR=/tmp/mpl

WORKDIR /app

# Dependencias primero (capa cacheable)
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY scripts ./scripts

RUN useradd --system --uid 10001 --home /app netsentinel \
    && mkdir -p /data/ingest /data/dataset /data/reports /data/ml \
    && chown -R netsentinel /data /app
USER netsentinel

EXPOSE 8000

# Migraciones -> semilla idempotente -> API
CMD ["sh", "-c", "python -m app.db.wait && alembic upgrade head && python -m app.db.seed && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]

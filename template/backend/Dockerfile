FROM python:3.12-slim-bookworm

# Install curl for healthchecks
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.5.7 /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy application files
COPY app ./app
COPY alembic.ini ./alembic.ini

# Install dependencies
COPY pyproject.toml ./
COPY README.md ./
COPY uv.lock ./
RUN uv sync --frozen

EXPOSE 9095

CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn --host=0.0.0.0 --port=9095 --factory app.main:create_app"]

# syntax=docker/dockerfile:1.7

# ---------------------------------------------------------------------------
# Stage 1 — build the virtualenv with uv.
# Dependencies are installed BEFORE the app code is copied, so editing app/
# reuses the cached dependency layer instead of reinstalling everything.
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS builder

# Pinned uv binary — no apt/pip bootstrap needed.
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Dependency layer: only invalidated when the manifests change.
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Application layer: changes here never rebuild the dependency layer.
COPY app ./app
COPY alembic.ini ./

# ---------------------------------------------------------------------------
# Stage 2 — runtime. Ships the venv + app only, no uv and no build cache.
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN useradd --create-home --uid 10001 app

WORKDIR /app
COPY --from=builder --chown=app:app /app /app

USER app
EXPOSE 9095

# `exec` hands PID 1 to uvicorn so SIGTERM stops the server cleanly.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn --host=0.0.0.0 --port=9095 --factory app.main:create_app"]

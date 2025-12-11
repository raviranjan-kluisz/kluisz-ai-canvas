# syntax=docker/dockerfile:1
# Direct Backend-Only Build - No Frontend, No Intermediate Image
# Optimized to build ONLY what's needed for the backend

################################
# BUILDER STAGE
################################
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV RUSTFLAGS='--cfg reqwest_unstable'

# Install minimal build dependencies
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    build-essential \
    git \
    gcc \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY ./uv.lock /app/uv.lock
COPY ./README.md /app/README.md
COPY ./pyproject.toml /app/pyproject.toml
COPY ./src/backend/base/README.md /app/src/backend/base/README.md
COPY ./src/backend/base/uv.lock /app/src/backend/base/uv.lock
COPY ./src/backend/base/pyproject.toml /app/src/backend/base/pyproject.toml
COPY ./src/lfx/README.md /app/src/lfx/README.md
COPY ./src/lfx/pyproject.toml /app/src/lfx/pyproject.toml
COPY ./src/klx/README.md /app/src/klx/README.md
COPY ./src/klx/pyproject.toml /app/src/klx/pyproject.toml

# Install Python dependencies (no dev dependencies)
RUN --mount=type=cache,target=/root/.cache/uv \
    RUSTFLAGS='--cfg reqwest_unstable' \
    uv sync --frozen --no-install-project --no-editable --no-dev --extra postgresql

# Copy source code
COPY ./src /app/src

# Final package install
RUN --mount=type=cache,target=/root/.cache/uv \
    RUSTFLAGS='--cfg reqwest_unstable' \
    uv sync --frozen --no-editable --no-dev --extra postgresql

# Cleanup unnecessary files
RUN find /app/.venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true \
    && find /app/.venv -type f -name "*.pyc" -delete \
    && find /app/.venv -type f -name "*.pyo" -delete \
    && find /app/.venv -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true \
    && find /app/.venv -type d -name "test" -exec rm -rf {} + 2>/dev/null || true

################################
# RUNTIME - Minimal Backend-Only
################################
FROM python:3.12.3-slim AS runtime

# Install ONLY runtime dependencies (no build tools, no Node.js!)
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    curl \
    libpq5 \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && useradd user -u 1000 -g 0 --no-create-home --home-dir /app/data

# Copy only the Python virtual environment
COPY --from=builder --chown=1000 /app/.venv /app/.venv

# Set environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONFAULTHANDLER=1
ENV KLUISZ_HOST=0.0.0.0
ENV KLUISZ_PORT=7860

LABEL org.opencontainers.image.title=kluisz-backend
LABEL org.opencontainers.image.authors=['Kluisz Kanvas']
LABEL org.opencontainers.image.licenses=MIT

USER user
WORKDIR /app

# Run as backend-only (no frontend)
CMD ["kluisz", "run", "--host", "0.0.0.0", "--port", "7860", "--backend-only"]




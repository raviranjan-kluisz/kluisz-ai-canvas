# syntax=docker/dockerfile:1
# Optimized Dockerfile to reduce image size from 5.3GB to <2GB

################################
# BUILDER-BASE
# Used to build deps + create our virtual environment
################################
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# Enable bytecode compilation
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
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy only necessary files for dependency installation
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

# Install Python dependencies (without dev dependencies)
RUN --mount=type=cache,target=/root/.cache/uv \
    RUSTFLAGS='--cfg reqwest_unstable' \
    uv sync --frozen --no-install-project --no-editable --no-dev --extra postgresql

# Copy source code
COPY ./src /app/src

################################
# FRONTEND BUILDER
# Build frontend separately to avoid including node_modules
################################
FROM node:20-slim AS frontend-builder

WORKDIR /tmp/frontend
COPY src/frontend/package*.json ./
RUN npm install --legacy-peer-deps \
    && npm install @chakra-ui/system @chakra-ui/react @emotion/react @emotion/styled framer-motion --legacy-peer-deps

COPY src/frontend ./
RUN ESBUILD_BINARY_PATH="" NODE_OPTIONS="--max-old-space-size=8192" JOBS=1 npm run build

################################
# PYTHON FINAL INSTALL
################################
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS python-installer

WORKDIR /app
COPY --from=builder /app /app

# Copy built frontend
COPY --from=frontend-builder /tmp/frontend/build /app/src/backend/base/kluisz/frontend

# Final Python package install
RUN --mount=type=cache,target=/root/.cache/uv \
    RUSTFLAGS='--cfg reqwest_unstable' \
    uv sync --frozen --no-editable --no-dev --extra postgresql \
    && find /app/.venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true \
    && find /app/.venv -type f -name "*.pyc" -delete \
    && find /app/.venv -type f -name "*.pyo" -delete \
    && find /app/.venv -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true \
    && find /app/.venv -type d -name "test" -exec rm -rf {} + 2>/dev/null || true

################################
# RUNTIME - Minimal final image
################################
FROM python:3.12.3-slim AS runtime

# Install only runtime dependencies (no build tools!)
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    curl \
    libpq5 \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && useradd user -u 1000 -g 0 --no-create-home --home-dir /app/data

# Copy only the virtual environment
COPY --from=python-installer --chown=1000 /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV KLUISZ_HOST=0.0.0.0
ENV KLUISZ_PORT=7860

LABEL org.opencontainers.image.title=kluisz
LABEL org.opencontainers.image.authors=['Kluisz Kanvas']
LABEL org.opencontainers.image.licenses=MIT
LABEL org.opencontainers.image.url=https://github.com/kluisz/kluisz-ai-canvas
LABEL org.opencontainers.image.source=https://github.com/kluisz/kluisz-ai-canvas

USER user
WORKDIR /app

CMD ["kluisz", "run"]



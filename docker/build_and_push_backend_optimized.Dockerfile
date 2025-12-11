# syntax=docker/dockerfile:1
# Backend-only optimized Dockerfile
# Takes the base optimized image and removes frontend

ARG KLUISZ_IMAGE=mohan021/kluisz:latest
FROM ${KLUISZ_IMAGE}

# Remove frontend to make it backend-only
RUN rm -rf /app/.venv/lib/python3.12/site-packages/kluisz/frontend 2>/dev/null || true

# Run as backend-only
CMD ["kluisz", "run", "--host", "0.0.0.0", "--port", "7860", "--backend-only"]



# syntax=docker/dockerfile:1
# Keep this syntax directive! It's used to enable Docker BuildKit

ARG KLUISZ_IMAGE
FROM ${KLUISZ_IMAGE}

RUN rm -rf /app/.venv/kluisz/frontend

CMD ["python", "-m", "kluisz", "run", "--host", "0.0.0.0", "--port", "7860", "--backend-only"]

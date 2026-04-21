# syntax=docker/dockerfile:1.7

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential curl libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 依赖先行，利用 layer cache
COPY algo/pyproject.toml algo/README.md algo/
COPY algo/liveguard_algo algo/liveguard_algo
COPY backend/pyproject.toml backend/README.md backend/
COPY backend/liveguard_backend backend/liveguard_backend
COPY backend/alembic backend/alembic
COPY backend/alembic.ini backend/alembic.ini
COPY backend/scripts backend/scripts

RUN pip install --upgrade pip wheel \
    && pip install -e ./algo \
    && pip install -e ./backend

EXPOSE 8080

CMD ["uvicorn", "liveguard_backend.main:app", "--host", "0.0.0.0", "--port", "8080", "--proxy-headers"]

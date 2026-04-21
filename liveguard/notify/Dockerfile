# syntax=docker/dockerfile:1.7

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY notify/pyproject.toml notify/README.md notify/
COPY notify/liveguard_notify notify/liveguard_notify

RUN pip install --upgrade pip wheel \
    && pip install -e ./notify

EXPOSE 8081

CMD ["uvicorn", "liveguard_notify.main:app", "--host", "0.0.0.0", "--port", "8081"]

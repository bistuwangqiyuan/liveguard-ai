"""健康检查与 metrics。"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from ... import __version__
from ...infra.metrics import metrics_response
from ..schemas import HealthStatus

router = APIRouter(tags=["system"])


@router.get("/healthz", response_model=HealthStatus, summary="liveness probe")
async def healthz() -> HealthStatus:
    return HealthStatus(
        service="liveguard-backend",
        version=__version__,
        status="ok",
        timestamp=datetime.now(UTC),
        checks={"process": "ok"},
    )


@router.get("/readyz", response_model=HealthStatus, summary="readiness probe")
async def readyz() -> HealthStatus:
    # 实战中会异步 ping DB / Redis / Kafka；这里简单返回。
    return HealthStatus(
        service="liveguard-backend",
        version=__version__,
        status="ready",
        timestamp=datetime.now(UTC),
        checks={"db": "up", "cache": "up", "bus": "up"},
    )


@router.get("/metrics", summary="prometheus metrics")
async def metrics():  # noqa: D401
    return metrics_response()
